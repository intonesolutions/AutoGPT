-- AlterTable
ALTER TABLE "AgentGraphExecution" ADD COLUMN     "variables" JSONB;

-- CreateTable
CREATE TABLE "AgentPersistentVarData" (
    "agentGraphId" TEXT NOT NULL,
    "variables" JSONB,

    CONSTRAINT "AgentPersistentVarData_pkey" PRIMARY KEY ("agentGraphId")
);
