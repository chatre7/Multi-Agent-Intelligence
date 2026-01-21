"""
Advanced Agent Ecosystem - Specialized Agents

Collection of specialized agents for different domains and use cases,
extending the core agent capabilities with domain expertise.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from database_manager import get_database_manager

logger = logging.getLogger(__name__)


# ==========================================
# BASE SPECIALIZED AGENT CLASS
# ==========================================


class SpecializedAgent:
    """Base class for specialized agents with domain expertise"""

    def __init__(self, name: str, domain: str, expertise_level: str = "expert"):
        self.name = name
        self.domain = domain
        self.expertise_level = expertise_level
        self.llm = ChatOllama(model="gpt-oss:120b-cloud", temperature=0.1)
        self.db = get_database_manager()

        # Agent capabilities and tools
        self.capabilities = []
        self.tools = []
        self.performance_metrics = {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "user_satisfaction": 0.0,
        }

    def get_system_prompt(self) -> str:
        """Get the specialized system prompt for this agent"""
        return f"""
        You are {self.name}, a {self.expertise_level} specialist in {self.domain}.

        Your capabilities: {", ".join(self.capabilities)}

        Guidelines:
        1. Stay focused on your domain expertise
        2. Provide detailed, actionable insights
        3. Use available tools when appropriate
        4. Maintain professional and helpful tone
        5. Always validate your recommendations
        6. Ask for clarification when needed

        Respond clearly and provide evidence for your recommendations.
        """

    async def process_task(
        self, task: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a task using domain expertise"""
        start_time = asyncio.get_event_loop().time()

        try:
            # Create system prompt
            system_prompt = self.get_system_prompt()

            # Add context if provided
            if context:
                system_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"

            # Process task
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Task: {task}"),
            ]

            response = await self.llm.ainvoke(messages)

            # Record performance metrics
            end_time = asyncio.get_event_loop().time()
            duration_ms = int((end_time - start_time) * 1000)

            await self.record_performance(task, True, duration_ms, response.content)

            return {
                "agent": self.name,
                "domain": self.domain,
                "response": response.content,
                "confidence": self._calculate_confidence(response.content),
                "processing_time_ms": duration_ms,
                "tools_used": [],  # Will be populated if tools are used
                "recommendations": self._extract_recommendations(response.content),
            }

        except Exception as e:
            logger.error(f"Agent {self.name} failed to process task: {e}")

            # Record failure
            end_time = asyncio.get_event_loop().time()
            duration_ms = int((end_time - start_time) * 1000)
            await self.record_performance(task, False, duration_ms, str(e))

            return {
                "agent": self.name,
                "domain": self.domain,
                "error": str(e),
                "processing_time_ms": duration_ms,
                "fallback_suggestions": self._get_fallback_suggestions(),
            }

    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score for the response"""
        # Simple heuristic-based confidence calculation
        confidence_indicators = [
            "confident",
            "certain",
            "definitely",
            "absolutely",
            "recommend",
            "suggest",
            "should",
            "must",
            "evidence",
            "data shows",
            "research indicates",
        ]

        response_lower = response.lower()
        matches = sum(
            1 for indicator in confidence_indicators if indicator in response_lower
        )

        # Normalize to 0-1 scale
        confidence = min(matches / 3.0, 1.0)
        return round(confidence, 2)

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract actionable recommendations from response"""
        recommendations = []

        # Look for numbered lists, bullet points, or recommendation keywords
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(
                ("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "-", "•", "*")
            ) or any(
                word in line.lower()
                for word in ["recommend", "suggest", "should", "must", "consider"]
            ):
                if len(line) > 10:  # Filter out very short lines
                    recommendations.append(line)

        return recommendations[:5]  # Limit to top 5 recommendations

    def _get_fallback_suggestions(self) -> List[str]:
        """Get fallback suggestions when agent fails"""
        return [
            f"Consult {self.domain} documentation",
            f"Search for '{self.domain}' best practices",
            f"Consider reaching out to {self.domain} specialists",
            f"Break down the problem into smaller {self.domain} tasks",
        ]

    async def record_performance(
        self, task: str, success: bool, duration_ms: int, response: str
    ):
        """Record performance metrics in database"""
        try:
            # Calculate token count (rough estimate)
            token_count = len(response.split()) * 1.3  # Rough token estimation

            await self.db.record_agent_metric(
                agent_name=self.name,
                operation=f"{self.domain}_task",
                duration_ms=duration_ms,
                token_count=int(token_count),
                success=success,
                metadata={
                    "domain": self.domain,
                    "task_length": len(task),
                    "response_length": len(response),
                },
            )

            # Update local metrics
            self.performance_metrics["tasks_completed"] += 1
            if success:
                # Rolling average for response time
                current_avg = self.performance_metrics["average_response_time"]
                new_avg = (current_avg + duration_ms) / 2
                self.performance_metrics["average_response_time"] = new_avg

                # Update success rate
                total_tasks = self.performance_metrics["tasks_completed"]
                success_rate = (success_rate * (total_tasks - 1) + 1) / total_tasks
                self.performance_metrics["success_rate"] = success_rate

        except Exception as e:
            logger.error(f"Failed to record performance for {self.name}: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        # Get stats from database for last 7 days
        db_stats = self.db.get_agent_performance_stats(self.name, days=7)

        return {
            "agent_name": self.name,
            "domain": self.domain,
            "expertise_level": self.expertise_level,
            "capabilities": self.capabilities,
            "performance": self.performance_metrics,
            "recent_stats": db_stats,
        }


# ==========================================
# SPECIALIZED AGENT IMPLEMENTATIONS
# ==========================================


class CodeReviewAgent(SpecializedAgent):
    """Advanced code review and security analysis agent"""

    def __init__(self):
        super().__init__("CodeReviewAgent", "code review and security", "senior")
        self.capabilities = [
            "Static code analysis",
            "Security vulnerability detection",
            "Code quality assessment",
            "Performance optimization suggestions",
            "Best practices compliance",
            "Test coverage analysis",
        ]

    def get_system_prompt(self) -> str:
        base_prompt = super().get_system_prompt()

        return (
            base_prompt
            + """

        As a senior code reviewer, focus on:

        SECURITY ANALYSIS:
        - SQL injection vulnerabilities
        - XSS (Cross-Site Scripting) risks
        - Authentication/authorization flaws
        - Data exposure risks
        - Input validation weaknesses

        CODE QUALITY:
        - Code maintainability and readability
        - Design pattern compliance
        - Error handling robustness
        - Documentation completeness
        - Performance bottlenecks

        TESTING:
        - Unit test coverage gaps
        - Integration test requirements
        - Edge case handling
        - Error scenario coverage

        Provide specific line-by-line feedback with severity levels:
        - 🔴 CRITICAL: Security vulnerabilities, data loss risks
        - 🟡 WARNING: Code quality issues, performance problems
        - 🟢 INFO: Suggestions for improvement, best practices
        """
        )

    def _calculate_confidence(self, response: str) -> float:
        """Enhanced confidence calculation for code review"""
        base_confidence = super()._calculate_confidence(response)

        # Boost confidence for code review specific indicators
        code_indicators = [
            "vulnerability",
            "security",
            "injection",
            "xss",
            "maintainability",
            "readability",
            "performance",
            "test coverage",
            "edge case",
            "error handling",
        ]

        response_lower = response.lower()
        code_matches = sum(
            1 for indicator in code_indicators if indicator in response_lower
        )

        # Add bonus confidence for technical depth
        technical_bonus = min(code_matches * 0.1, 0.3)
        return min(base_confidence + technical_bonus, 1.0)


class ResearchAgent(SpecializedAgent):
    """Academic research and synthesis agent"""

    def __init__(self):
        super().__init__("ResearchAgent", "academic research and analysis", "expert")
        self.capabilities = [
            "Academic paper analysis",
            "Research methodology evaluation",
            "Literature review synthesis",
            "Trend analysis and forecasting",
            "Evidence-based recommendations",
            "Citation and reference validation",
        ]

    def get_system_prompt(self) -> str:
        base_prompt = super().get_system_prompt()

        return (
            base_prompt
            + """

        As an expert research agent, focus on:

        METHODOLOGY ANALYSIS:
        - Research design validity
        - Sample size and statistical power
        - Control group appropriateness
        - Bias detection and mitigation

        EVIDENCE SYNTHESIS:
        - Cross-study comparison
        - Meta-analysis capabilities
        - Conflicting evidence resolution
        - Research gap identification

        TREND ANALYSIS:
        - Technology adoption curves
        - Market trend forecasting
        - Innovation trajectory mapping
        - Competitive landscape analysis

        QUALITY ASSURANCE:
        - Source credibility assessment
        - Publication quality evaluation
        - Peer review status verification
        - Research reproducibility checking

        Provide evidence-based conclusions with confidence intervals where applicable.
        Always cite sources and methodologies used in analysis.
        """
        )

    async def process_task(
        self, task: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced research processing with evidence gathering"""
        # Add research-specific context
        if context is None:
            context = {}

        context.update(
            {
                "research_focus": "academic rigor and evidence quality",
                "required_evidence": "peer-reviewed sources preferred",
                "methodology_check": "statistical validity and research design",
            }
        )

        result = await super().process_task(task, context)

        # Add research-specific metadata
        if "response" in result:
            result["research_metadata"] = {
                "evidence_quality": self._assess_evidence_quality(result["response"]),
                "methodology_score": self._score_methodology(result["response"]),
                "recommendation_strength": "strong"
                if result["confidence"] > 0.8
                else "moderate",
            }

        return result

    def _assess_evidence_quality(self, response: str) -> str:
        """Assess the quality of evidence in the response"""
        quality_indicators = {
            "high": [
                "randomized controlled trial",
                "meta-analysis",
                "systematic review",
                "peer-reviewed",
            ],
            "medium": ["case study", "survey", "expert opinion", "published study"],
            "low": ["anecdotal", "blog post", "social media", "unverified"],
        }

        response_lower = response.lower()

        for level, indicators in quality_indicators.items():
            if any(indicator in response_lower for indicator in indicators):
                return level

        return "unknown"

    def _score_methodology(self, response: str) -> float:
        """Score the methodological rigor mentioned"""
        methodology_keywords = [
            "methodology",
            "method",
            "approach",
            "design",
            "sample",
            "control",
            "variable",
            "hypothesis",
            "statistical",
            "analysis",
        ]

        response_lower = response.lower()
        matches = sum(
            1 for keyword in methodology_keywords if keyword in response_lower
        )

        return min(matches * 0.2, 1.0)


class DataAnalysisAgent(SpecializedAgent):
    """Statistical analysis and data visualization agent"""

    def __init__(self):
        super().__init__(
            "DataAnalysisAgent", "data analysis and visualization", "expert"
        )
        self.capabilities = [
            "Statistical analysis and modeling",
            "Data visualization design",
            "Trend analysis and forecasting",
            "Correlation and causation analysis",
            "Performance metrics optimization",
            "A/B testing analysis",
        ]

    def get_system_prompt(self) -> str:
        base_prompt = super().get_system_prompt()

        return (
            base_prompt
            + """

        As a data analysis expert, focus on:

        STATISTICAL ANALYSIS:
        - Descriptive statistics (mean, median, mode, variance)
        - Inferential statistics (hypothesis testing, confidence intervals)
        - Correlation analysis (Pearson, Spearman coefficients)
        - Regression modeling (linear, logistic, multivariate)

        DATA VISUALIZATION:
        - Chart type selection (bar, line, scatter, heatmap)
        - Color scheme optimization for accessibility
        - Data storytelling techniques
        - Interactive visualization recommendations

        TREND ANALYSIS:
        - Time series decomposition (trend, seasonal, residual)
        - Forecasting models (ARIMA, exponential smoothing)
        - Anomaly detection algorithms
        - Performance attribution analysis

        QUALITY ASSURANCE:
        - Data quality assessment (missing values, outliers)
        - Statistical assumption verification
        - Model validation techniques
        - Result interpretation accuracy

        Provide actionable insights with statistical significance levels.
        Include confidence intervals for key metrics.
        Recommend appropriate visualization types for each analysis.
        """
        )

    async def process_task(
        self, task: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced data analysis with statistical rigor"""
        result = await super().process_task(task, context)

        if "response" in result:
            result["analysis_metadata"] = {
                "statistical_methods_used": self._extract_statistical_methods(
                    result["response"]
                ),
                "visualization_recommendations": self._extract_visualization_needs(
                    result["response"]
                ),
                "confidence_level": "95%" if result["confidence"] > 0.8 else "80%",
            }

        return result

    def _extract_statistical_methods(self, response: str) -> List[str]:
        """Extract statistical methods mentioned in the response"""
        methods = [
            "regression",
            "correlation",
            "hypothesis test",
            "anova",
            "chi-square",
            "t-test",
            "f-test",
            "confidence interval",
            "p-value",
            "significance",
            "mean",
            "median",
            "mode",
            "variance",
            "standard deviation",
        ]

        response_lower = response.lower()
        found_methods = [method for method in methods if method in response_lower]

        return list(set(found_methods))  # Remove duplicates

    def _extract_visualization_needs(self, response: str) -> List[str]:
        """Extract visualization recommendations"""
        viz_types = [
            "bar chart",
            "line chart",
            "scatter plot",
            "histogram",
            "box plot",
            "heatmap",
            "pie chart",
            "dashboard",
            "time series",
            "correlation matrix",
        ]

        response_lower = response.lower()
        found_viz = [viz for viz in viz_types if viz in response_lower]

        return list(set(found_viz))


class DocumentationAgent(SpecializedAgent):
    """API documentation generation and maintenance agent"""

    def __init__(self):
        super().__init__("DocumentationAgent", "technical documentation", "expert")
        self.capabilities = [
            "API documentation generation",
            "Code documentation improvement",
            "README and guide creation",
            "Technical writing optimization",
            "Documentation maintenance",
            "User guide development",
        ]

    def get_system_prompt(self) -> str:
        base_prompt = super().get_system_prompt()

        return (
            base_prompt
            + """

        As a technical documentation expert, focus on:

        API DOCUMENTATION:
        - RESTful API endpoint documentation
        - Request/response schema definitions
        - Authentication and authorization details
        - Error code documentation
        - Example usage and code samples

        CODE DOCUMENTATION:
        - Function and method documentation
        - Class and module docstrings
        - Inline comment optimization
        - README file generation
        - Architecture documentation

        USER GUIDES:
        - Getting started tutorials
        - Feature walkthroughs
        - Troubleshooting guides
        - Best practices documentation
        - FAQ creation and maintenance

        QUALITY STANDARDS:
        - Clarity and readability assessment
        - Completeness verification
        - Technical accuracy validation
        - Consistency checking
        - Accessibility compliance

        Follow documentation best practices (clear, concise, comprehensive).
        Use appropriate formatting and structure for different document types.
        Ensure all code examples are tested and functional.
        """
        )

    async def process_task(
        self, task: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced documentation processing"""
        result = await super().process_task(task, context)

        if "response" in result:
            result["documentation_metadata"] = {
                "document_type": self._identify_document_type(task),
                "readability_score": self._assess_readability(result["response"]),
                "completeness_score": self._check_completeness(result["response"]),
                "technical_accuracy": self._validate_technical_content(
                    result["response"]
                ),
            }

        return result

    def _identify_document_type(self, task: str) -> str:
        """Identify the type of documentation being created"""
        task_lower = task.lower()

        if any(
            word in task_lower for word in ["api", "endpoint", "swagger", "openapi"]
        ):
            return "API Documentation"
        elif any(
            word in task_lower for word in ["readme", "getting started", "tutorial"]
        ):
            return "User Guide"
        elif any(
            word in task_lower for word in ["function", "class", "method", "docstring"]
        ):
            return "Code Documentation"
        elif any(word in task_lower for word in ["architecture", "system", "design"]):
            return "Technical Documentation"
        else:
            return "General Documentation"

    def _assess_readability(self, content: str) -> str:
        """Assess documentation readability"""
        # Simple readability metrics
        sentences = len(re.split(r"[.!?]+", content))
        words = len(content.split())
        avg_words_per_sentence = words / max(sentences, 1)

        if avg_words_per_sentence < 15:
            return "excellent"
        elif avg_words_per_sentence < 20:
            return "good"
        elif avg_words_per_sentence < 25:
            return "fair"
        else:
            return "needs_improvement"

    def _check_completeness(self, content: str) -> float:
        """Check documentation completeness"""
        completeness_indicators = [
            "example",
            "usage",
            "parameter",
            "return",
            "error",
            "installation",
            "configuration",
            "troubleshooting",
        ]

        content_lower = content.lower()
        matches = sum(
            1 for indicator in completeness_indicators if indicator in content_lower
        )

        return min(matches / len(completeness_indicators), 1.0)

    def _validate_technical_content(self, content: str) -> str:
        """Validate technical accuracy of documentation"""
        # Check for common technical documentation patterns
        technical_indicators = [
            "function",
            "method",
            "class",
            "parameter",
            "return",
            "import",
            "exception",
            "example",
            "code",
        ]

        content_lower = content.lower()
        technical_matches = sum(
            1 for indicator in technical_indicators if indicator in content_lower
        )

        if technical_matches > 5:
            return "high"
        elif technical_matches > 2:
            return "medium"
        else:
            return "low"


class DevOpsAgent(SpecializedAgent):
    """CI/CD pipeline management and deployment agent"""

    def __init__(self):
        super().__init__("DevOpsAgent", "DevOps and infrastructure", "expert")
        self.capabilities = [
            "CI/CD pipeline design and implementation",
            "Infrastructure as Code (IaC) development",
            "Containerization and orchestration",
            "Monitoring and logging setup",
            "Security scanning and compliance",
            "Performance optimization and scaling",
        ]

    def get_system_prompt(self) -> str:
        base_prompt = super().get_system_prompt()

        return (
            base_prompt
            + """

        As a DevOps expert, focus on:

        CI/CD PIPELINES:
        - Pipeline design and optimization
        - Automated testing integration
        - Deployment strategy development
        - Rollback and recovery procedures
        - Pipeline security and access control

        INFRASTRUCTURE:
        - Cloud architecture design
        - Container orchestration (Docker, Kubernetes)
        - Infrastructure as Code (Terraform, CloudFormation)
        - Monitoring and alerting setup
        - Scalability and performance optimization

        SECURITY & COMPLIANCE:
        - Security scanning integration
        - Vulnerability assessment
        - Compliance automation (SOC2, GDPR, HIPAA)
        - Access control and permissions
        - Audit logging and monitoring

        DEPLOYMENT STRATEGIES:
        - Blue-green deployments
        - Canary releases
        - Feature flags and toggles
        - Database migration strategies
        - Zero-downtime deployment techniques

        Provide production-ready solutions with monitoring, logging, and rollback capabilities.
        Always consider security, scalability, and maintainability in recommendations.
        Include specific tool and platform recommendations with justification.
        """
        )

    async def process_task(
        self, task: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Enhanced DevOps processing with infrastructure considerations"""
        result = await super().process_task(task, context)

        if "response" in result:
            result["devops_metadata"] = {
                "infrastructure_tools": self._extract_infrastructure_tools(
                    result["response"]
                ),
                "deployment_strategy": self._identify_deployment_strategy(
                    result["response"]
                ),
                "security_measures": self._extract_security_measures(
                    result["response"]
                ),
                "scalability_considerations": self._assess_scalability(
                    result["response"]
                ),
            }

        return result

    def _extract_infrastructure_tools(self, response: str) -> List[str]:
        """Extract infrastructure tools mentioned"""
        tools = [
            "docker",
            "kubernetes",
            "terraform",
            "ansible",
            "jenkins",
            "github actions",
            "gitlab ci",
            "aws",
            "azure",
            "gcp",
            "nginx",
            "apache",
            "prometheus",
            "grafana",
        ]

        response_lower = response.lower()
        found_tools = [tool for tool in tools if tool in response_lower]

        return list(set(found_tools))

    def _identify_deployment_strategy(self, response: str) -> str:
        """Identify deployment strategy recommended"""
        strategies = {
            "blue-green": ["blue-green", "blue green"],
            "canary": ["canary"],
            "rolling": ["rolling", "rolling update"],
            "recreate": ["recreate"],
            "feature flags": ["feature flag", "feature toggle"],
        }

        response_lower = response.lower()
        for strategy, keywords in strategies.items():
            if any(keyword in response_lower for keyword in keywords):
                return strategy

        return "standard"

    def _extract_security_measures(self, response: str) -> List[str]:
        """Extract security measures mentioned"""
        measures = [
            "ssl/tls",
            "encryption",
            "authentication",
            "authorization",
            "firewall",
            "intrusion detection",
            "logging",
            "monitoring",
            "vulnerability scanning",
            "compliance",
            "audit",
        ]

        response_lower = response.lower()
        found_measures = [measure for measure in measures if measure in response_lower]

        return list(set(found_measures))

    def _assess_scalability(self, response: str) -> str:
        """Assess scalability considerations"""
        scalability_indicators = [
            "load balancer",
            "auto scaling",
            "horizontal scaling",
            "caching",
            "database optimization",
            "cdn",
            "microservices",
            "serverless",
        ]

        response_lower = response.lower()
        matches = sum(
            1 for indicator in scalability_indicators if indicator in response_lower
        )

        if matches >= 3:
            return "high_scalability_focus"
        elif matches >= 1:
            return "moderate_scalability_focus"
        else:
            return "basic_scalability"


# ==========================================
# AGENT REGISTRY & ORCHESTRATION
# ==========================================


class AgentRegistry:
    """Registry for managing specialized agents"""

    def __init__(self):
        self.agents: Dict[str, SpecializedAgent] = {}
        self._register_builtin_agents()

    def _register_builtin_agents(self):
        """Register built-in specialized agents"""
        self.register_agent(CodeReviewAgent())
        self.register_agent(ResearchAgent())
        self.register_agent(DataAnalysisAgent())
        self.register_agent(DocumentationAgent())
        self.register_agent(DevOpsAgent())

    def register_agent(self, agent: SpecializedAgent):
        """Register a specialized agent"""
        self.agents[agent.name] = agent
        logger.info(f"Registered specialized agent: {agent.name} ({agent.domain})")

    def get_agent(self, name: str) -> Optional[SpecializedAgent]:
        """Get an agent by name"""
        return self.agents.get(name)

    def get_agents_by_domain(self, domain: str) -> List[SpecializedAgent]:
        """Get agents by domain expertise"""
        return [
            agent
            for agent in self.agents.values()
            if domain.lower() in agent.domain.lower()
        ]

    def get_all_agents(self) -> List[SpecializedAgent]:
        """Get all registered agents"""
        return list(self.agents.values())

    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities summary for all agents"""
        return {name: agent.capabilities for name, agent in self.agents.items()}


# Global registry instance
_agent_registry = None


def get_agent_registry() -> AgentRegistry:
    """Get or create the global agent registry"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


# ==========================================
# MULTI-AGENT ORCHESTRATION
# ==========================================


class MultiAgentOrchestrator:
    """Orchestrates multiple specialized agents for complex tasks"""

    def __init__(self):
        self.registry = get_agent_registry()
        self.db = get_database_manager()

    async def orchestrate_task(
        self, task: str, strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        Orchestrate a complex task across multiple agents

        Args:
            task: The complex task to orchestrate
            strategy: Orchestration strategy ("auto", "sequential", "parallel", "consensus")

        Returns:
            Orchestrated results from multiple agents
        """
        if strategy == "auto":
            strategy = self._determine_optimal_strategy(task)

        if strategy == "sequential":
            return await self._sequential_orchestration(task)
        elif strategy == "parallel":
            return await self._parallel_orchestration(task)
        elif strategy == "consensus":
            return await self._consensus_orchestration(task)
        else:
            return await self._parallel_orchestration(task)

    def _determine_optimal_strategy(self, task: str) -> str:
        """Determine the optimal orchestration strategy based on task characteristics"""
        task_lower = task.lower()

        # Consensus for decision-making tasks
        if any(
            word in task_lower
            for word in ["choose", "select", "decide", "recommend", "which"]
        ):
            return "consensus"

        # Sequential for dependent tasks
        if any(
            word in task_lower
            for word in ["first", "then", "after", "following", "step by step"]
        ):
            return "sequential"

        # Parallel for independent subtasks
        if any(
            word in task_lower
            for word in ["analyze", "review", "check", "validate", "multiple"]
        ):
            return "parallel"

        return "parallel"  # Default

    async def _sequential_orchestration(self, task: str) -> Dict[str, Any]:
        """Execute tasks sequentially through different agents"""
        results = []
        current_task = task

        # Define agent sequence based on task type
        agent_sequence = self._get_sequential_sequence(task)

        for agent_name in agent_sequence:
            agent = self.registry.get_agent(agent_name)
            if agent:
                result = await agent.process_task(current_task)
                results.append(result)

                # Use output from previous agent as input for next
                if "response" in result:
                    current_task = f"Previous result: {result['response']}\n\nContinue with: {task}"

        return {
            "strategy": "sequential",
            "agent_sequence": agent_sequence,
            "results": results,
            "final_result": results[-1] if results else None,
        }

    async def _parallel_orchestration(self, task: str) -> Dict[str, Any]:
        """Execute tasks in parallel across multiple agents"""
        # Select relevant agents for the task
        relevant_agents = self._select_relevant_agents(task)

        # Execute in parallel
        tasks = []
        for agent in relevant_agents:
            task_coro = agent.process_task(task)
            tasks.append(task_coro)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"agent": relevant_agents[i].name, "error": str(result)}
                )
            else:
                processed_results.append(result)

        return {
            "strategy": "parallel",
            "agents_used": [agent.name for agent in relevant_agents],
            "results": processed_results,
            "synthesis": self._synthesize_parallel_results(processed_results),
        }

    async def _consensus_orchestration(self, task: str) -> Dict[str, Any]:
        """Get consensus from multiple agents on a decision"""
        # Select agents for consensus
        consensus_agents = self._select_consensus_agents(task)

        # Get opinions from all agents
        tasks = [agent.process_task(task) for agent in consensus_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and find consensus
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"agent": consensus_agents[i].name, "error": str(result)}
                )
            else:
                processed_results.append(result)

        consensus_result = self._calculate_consensus(processed_results)

        return {
            "strategy": "consensus",
            "agents_consulted": [agent.name for agent in consensus_agents],
            "individual_results": processed_results,
            "consensus": consensus_result,
        }

    def _get_sequential_sequence(self, task: str) -> List[str]:
        """Determine the optimal sequential agent order"""
        task_lower = task.lower()

        # Code review sequence
        if any(word in task_lower for word in ["review", "check", "validate", "code"]):
            return ["CodeReviewAgent", "DocumentationAgent", "DevOpsAgent"]

        # Research sequence
        elif any(word in task_lower for word in ["research", "analyze", "study"]):
            return ["ResearchAgent", "DataAnalysisAgent", "DocumentationAgent"]

        # Development sequence
        elif any(word in task_lower for word in ["develop", "build", "create"]):
            return ["DocumentationAgent", "CodeReviewAgent", "DevOpsAgent"]

        # Default sequence
        return ["ResearchAgent", "DataAnalysisAgent", "DocumentationAgent"]

    def _select_relevant_agents(self, task: str) -> List[SpecializedAgent]:
        """Select the most relevant agents for a task"""
        task_lower = task.lower()
        all_agents = self.registry.get_all_agents()

        # Score agents based on relevance to task
        agent_scores = {}
        for agent in all_agents:
            score = 0

            # Domain keyword matching
            domain_keywords = {
                "CodeReviewAgent": ["code", "review", "security", "bug", "quality"],
                "ResearchAgent": [
                    "research",
                    "study",
                    "analyze",
                    "evidence",
                    "academic",
                ],
                "DataAnalysisAgent": [
                    "data",
                    "statistics",
                    "chart",
                    "analysis",
                    "metrics",
                ],
                "DocumentationAgent": ["document", "write", "guide", "api", "readme"],
                "DevOpsAgent": [
                    "deploy",
                    "pipeline",
                    "infrastructure",
                    "ci/cd",
                    "server",
                ],
            }

            if agent.name in domain_keywords:
                keywords = domain_keywords[agent.name]
                score += sum(1 for keyword in keywords if keyword in task_lower)

            agent_scores[agent.name] = score

        # Select top 3 most relevant agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        top_agent_names = [name for name, score in sorted_agents[:3] if score > 0]

        # Return at least 2 agents, max 4
        if len(top_agent_names) < 2:
            top_agent_names = [name for name, score in sorted_agents[:2]]

        return [
            self.registry.get_agent(name)
            for name in top_agent_names
            if self.registry.get_agent(name)
        ]

    def _select_consensus_agents(self, task: str) -> List[SpecializedAgent]:
        """Select agents for consensus-based decision making"""
        # For consensus, use agents with different perspectives
        consensus_pool = ["ResearchAgent", "DataAnalysisAgent", "CodeReviewAgent"]

        return [
            self.registry.get_agent(name)
            for name in consensus_pool
            if self.registry.get_agent(name)
        ]

    def _synthesize_parallel_results(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize results from parallel agent execution"""
        if not results:
            return {"synthesis": "No results to synthesize"}

        # Extract key insights from each result
        insights = []
        recommendations = []
        confidence_scores = []

        for result in results:
            if "error" not in result:
                if "response" in result:
                    # Extract key insights (first 2-3 sentences)
                    response_sentences = result["response"].split(".")[:3]
                    insights.extend(response_sentences)

                if "recommendations" in result:
                    recommendations.extend(result["recommendations"])

                if "confidence" in result:
                    confidence_scores.append(result["confidence"])

        # Create synthesis
        synthesis = {
            "key_insights": list(set(insights))[:5],  # Unique insights, max 5
            "consolidated_recommendations": list(set(recommendations))[:5],
            "average_confidence": sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.5,
            "agent_contributions": len([r for r in results if "error" not in r]),
        }

        return synthesis

    def _calculate_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consensus from multiple agent opinions"""
        if not results:
            return {"consensus": "No results for consensus calculation"}

        valid_results = [r for r in results if "error" not in r]

        if not valid_results:
            return {"consensus": "All agents failed to provide opinions"}

        # Extract recommendations and weight by confidence
        recommendation_weights = {}

        for result in valid_results:
            confidence = result.get("confidence", 0.5)
            recommendations = result.get("recommendations", [])

            for rec in recommendations:
                if rec not in recommendation_weights:
                    recommendation_weights[rec] = 0
                recommendation_weights[rec] += confidence

        # Sort by consensus weight
        sorted_recs = sorted(
            recommendation_weights.items(), key=lambda x: x[1], reverse=True
        )

        consensus = {
            "top_recommendation": sorted_recs[0][0]
            if sorted_recs
            else "No clear consensus",
            "consensus_level": len(sorted_recs) / len(valid_results)
            if valid_results
            else 0,
            "all_recommendations": sorted_recs[:5],  # Top 5
            "agents_agreed": len(valid_results),
            "confidence_score": sum(r.get("confidence", 0.5) for r in valid_results)
            / len(valid_results),
        }

        return consensus


# Global orchestrator instance
_multi_agent_orchestrator = None


def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """Get or create the global multi-agent orchestrator"""
    global _multi_agent_orchestrator
    if _multi_agent_orchestrator is None:
        _multi_agent_orchestrator = MultiAgentOrchestrator()
    return _multi_agent_orchestrator
