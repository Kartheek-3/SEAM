import os

path = r"c:\Users\KARTHIK\Downloads\FYP1\SEAM\agents\coding\agent.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("    async def execute(self, input_data: AgentInput) -> AgentOutput:")
end_idx = len(content)

new_execute = """    async def execute(self, input_data: AgentInput) -> AgentOutput:
        start_time = time.time()
        logger.info(f"Task {input_data.task_id}: CodingAgent starting execution.")

        if not input_data.instructions.strip():
            return AgentOutput(
                task_id=input_data.task_id,
                agent_id=AgentRole.CODING,
                status=AgentStatus.FAILURE,
                result={},
                feedback="Instructions cannot be empty.",
                execution_time_ms=0
            )

        user_prompt = self._format_prompt(input_data)
        
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                raw_markdown = ""
                # Attempt to use WorkerPool directly to bypass JsonOutputParser
                if hasattr(self.llm, "worker_pool"):
                    import urllib.request
                    import urllib.parse
                    import json
                    import asyncio
                    
                    pool = self.llm.worker_pool
                    # Fallback to general model if not in worker client (should not happen in prod SEAM)
                    model_name = getattr(self.llm, "model_name", "llama3.1")
                    worker = await pool.select_worker(task_id=input_data.task_id, timeout=300.0)
                    is_infrastructure_failure = False
                    
                    try:
                        url = f"{worker.base_url}/api/generate"
                        full_prompt = f"{SYSTEM_PROMPT}\\n\\n{user_prompt}"
                        
                        data = {
                            "model": worker.model,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {"temperature": 0.1}
                        }
                        
                        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
                        
                        try:
                            response = await asyncio.to_thread(urllib.request.urlopen, req, timeout=300)
                            res_data = json.loads(response.read().decode('utf-8'))
                            raw_markdown = res_data.get('response', '')
                        except TimeoutError as e:
                            is_infrastructure_failure = True
                            raise LLMException("LLM generation timed out") from e
                        except Exception as e:
                            is_infrastructure_failure = True
                            raise LLMException(f"LLM generation failed: {e}") from e
                            
                    finally:
                        if is_infrastructure_failure:
                            pool.report_infrastructure_failure(worker.worker_id)
                        else:
                            pool.release_worker(worker.worker_id)
                else:
                    # Fallback for MockLLM in tests
                    # MockLLM generate_structured_output can just return the CodeGenerationResponse directly
                    response = await self.llm.generate_structured_output(
                        system_prompt=SYSTEM_PROMPT,
                        user_prompt=user_prompt,
                        response_model=CodeGenerationResponse
                    )
                    # We convert MockLLM response to fake markdown to feed to parser
                    lines = []
                    for f in response.files:
                        lines.append(f"<!-- path: {f.path} -->")
                        lines.append(f"```{f.language}")
                        lines.append(f.content)
                        lines.append("```")
                    raw_markdown = "\\n".join(lines)

                # Parse the raw markdown deterministically
                parsed_files = MarkdownParser.parse(raw_markdown)

                artifacts = []
                for idx, gen_file in enumerate(parsed_files):
                    self._validate_path(gen_file["path"])
                    
                    artifacts.append(
                        Artifact(
                            id=f"art-{input_data.task_id}-{idx}",
                            project_id=input_data.context.get("project_id", "unknown"),
                            task_id=input_data.task_id,
                            type=gen_file["artifact_type"],
                            name=gen_file["path"],
                            content=gen_file["content"],
                            language=gen_file["language"],
                            created_at=datetime.now(timezone.utc)
                        )
                    )

                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Task {input_data.task_id}: CodingAgent completed successfully in {execution_time}ms.")

                return AgentOutput(
                    task_id=input_data.task_id,
                    agent_id=AgentRole.CODING,
                    status=AgentStatus.SUCCESS,
                    result={"files_generated": len(artifacts)},
                    artifacts=artifacts,
                    execution_time_ms=execution_time
                )

            except (PathTraversalError, CodeGenerationError) as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                last_error = str(e)
                user_prompt += f"\\n\\nValidation Error: {last_error}. Please fix this and generate again. Return the required Markdown file format. Do not return JSON. Every source file must have: <!-- path: relative/path --> followed by a fenced code block."
            except LLMException as e:
                logger.warning(f"LLM generation error on attempt {attempt + 1}: {e}")
                last_error = str(e)
            except Exception as e:
                logger.error(f"LLM execution failed: {e}")
                return AgentOutput(
                    task_id=input_data.task_id,
                    agent_id=AgentRole.CODING,
                    status=AgentStatus.FAILURE,
                    result={},
                    feedback=f"LLM failure: {str(e)}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

        return AgentOutput(
            task_id=input_data.task_id,
            agent_id=AgentRole.CODING,
            status=AgentStatus.FAILURE,
            result={},
            feedback=f"Code generation failed after {max_retries} attempts. Last error: {last_error}",
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
"""

new_content = content[:start_idx] + new_execute
with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)
