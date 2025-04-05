"use client";
import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { GraphID } from "@/lib/autogpt-server-api/types";
import FlowEditor from "@/components/Flow";
export default function Home() {
  const query = useSearchParams();
  useEffect(() => {
      // Load jquery script
      const script = document.createElement("script");
      script.src = "https://code.jquery.com/jquery-3.7.1.slim.min.js";
      script.async = false;
      script.onload = () => {
        if (query.get("mode") === "1") {
          window.$("nav").hide();
        }
      };
      document.head.appendChild(script);
  },[query]);
  
  return (
    <FlowEditor
      className="flow-container"
      flowID={query.get("flowID") as GraphID | null ?? undefined}
      flowVersion={query.get("flowVersion") ?? undefined}
    />
  );
}
