import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal,List
from enum import Enum, EnumMeta
from pydantic import BaseModel, ConfigDict, SecretStr
from prisma.models import (AgentGraphExecution,AgentPersistentVarData)
from types import SimpleNamespace
from prisma import Prisma,Json
import asyncio
import re
import json
import copy
from dataclasses import dataclass, asdict
from prisma.types import (AgentGraphExecutionUpdateInput,AgentPersistentVarDataUpsertInput,AgentGraphExecutionCreateInput)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
    UserPasswordCredentials,
)
from backend.integrations.providers import ProviderName
@dataclass
class Variable:
    VarName: str
    VarValue: object
    Persistent: bool
async def update_graph_execution(
    user_id: str,
    execution_id: str,
    variables:dict[str, any] | None
) -> AgentGraphExecution | None:
    try:
        db=Prisma()
        await db.connect()
        vars=[]
        for item in variables:
            v=dict()
            v['VarName']=item.VarName
            v['VarValue']=item.VarValue
            v['Persistent']=False
            vars.append(v)
        data=Json(vars)
        
        execution = await db.agentgraphexecution.update(
            where={"id": execution_id, "isDeleted": False, "userId": user_id},
            data=AgentGraphExecutionUpdateInput(variables=data)
        )
        if not execution:
            return None
        await db.disconnect()
        return execution
    except Exception as e:
        msg=str(e)
        print(msg)

async def update_agent_persistvariabls(
    graph_id:str,
    variables:dict[str, any] | None
) -> AgentPersistentVarData:
    db=Prisma()
    await db.connect()
    vars=[]
    for item in variables:
        v=dict()
        v['VarName']=item.VarName
        v['VarValue']=item.VarValue
        v['Persistent']=True
        vars.append(v)
    data=Json(vars)
    execution = await db.agentpersistentvardata.upsert(where={"agentGraphId":graph_id},
        data=AgentPersistentVarDataUpsertInput(
            update=AgentGraphExecutionUpdateInput(agentGraphId=graph_id,variables=data),
            create=AgentGraphExecutionCreateInput(agentGraphId=graph_id,variables=data)
        )
    )
    if not execution:
        return None
    await db.disconnect()
    return execution

class PersistencyMode (str,Enum):
    EP="execution persistence (single execution)"
    AP="agent persistence (across all executions)"
class IntoneSetVariableBlock(Block):
    class Input(BlockSchema):
        outlets: List[str] = SchemaField(description="outlets to be used in the expression")
        target_variable: str = SchemaField(
            description="name of the target variable"
        )
        expression: str = SchemaField(
            description="RHS expression. use { {<var-name> or outlet[index] } } for replacements"
        )
        persistency_mode: PersistencyMode=SchemaField(description="persistency mode",default=PersistencyMode.EP)
        

    class Output(BlockSchema):
        value: str = SchemaField(description="value of the set variable")
        error: str = SchemaField(
            description="Error message if the email sending failed"
        )

    def __init__(self):
        super().__init__(
            id="aabbccdd-0000-1111-2222-000000000003",
            description="This block sets variable to an expression.",
            categories={BlockCategory.BASIC},
            input_schema=IntoneSetVariableBlock.Input,
            output_schema=IntoneSetVariableBlock.Output,
        )

    
    def run(
        self, input_data: Input, **kwargs
    ) -> BlockOutput:
        graph_exec_id=kwargs['graph_exec_id']
        graph_id=kwargs['graph_id']
        user_id=kwargs['user_id']
        variables=kwargs.get("variables") or []
        outlet_dict = [{"VarName":f"outlet[{i}]","VarValue":val} for i, val in enumerate(input_data.outlets)]
        outlet_dict = [SimpleNamespace(**item) for item in outlet_dict]

        merged_dict = {item.VarName: item for item in variables}
        for item in outlet_dict:
            merged_dict[item.VarName] = item
        vars = list(merged_dict.values()) 
        pattern = re.compile(r"\{\{([^\{]+)\}\}")
        expr=input_data.expression
        for item in vars:
            expr=pattern.sub(lambda m: f'(next((v for v in vars if v.VarName == "{item.VarName}"), None) or type("", (), {{"VarValue": None}})()).VarValue' if m.group(1) == item.VarName else m.group(0), expr)
        val=None
        scope={"vars":vars}
        exec("val=" + expr,scope)
        val=scope["val"]
        var_item={"VarName":input_data.target_variable,"VarValue":val,"Persistent":False}
        var_item=SimpleNamespace(**var_item)
        merged_dict = {item.VarName: item for item in variables}
        merged_dict[var_item.VarName] = var_item
        variables = list(merged_dict.values())
        asyncio.run(update_graph_execution(user_id=user_id,execution_id=graph_exec_id,variables=variables))
        if input_data.persistency_mode==PersistencyMode.AP:
            var_item.Persistent=True
            persistent_vars = [v for v in variables if v.Persistent]
            persistent_dict = {v.VarName: v for v in persistent_vars}
            persistent_dict[var_item.VarName] = var_item
            persistent_vars = list(persistent_dict.values())
            asyncio.run(update_agent_persistvariabls(graph_id=graph_id,variables=persistent_vars))
        vlstr=""
        try:
            valstr=json.dumps(val, default=str)
        except Exception as e:
            valstr=""
        yield "value",  valstr
