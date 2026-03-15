from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ClienteData:
    """Client profile data."""

    id: str
    nome_empresa: str
    nicho: str
    publico_alvo: dict = field(default_factory=dict)
    tom_de_voz: dict = field(default_factory=dict)
    pilares: list[dict] = field(default_factory=list)
    tipos_conteudo: list[dict] = field(default_factory=list)
    concorrentes: list[dict] = field(default_factory=list)
    instrucoes: str | None = None


@dataclass
class PesquisaResult:
    """Output of Pesquisador Agent."""

    tendencias: list[dict] = field(default_factory=list)  # [{termo, volume, contexto}]
    datas_comemorativas: list[dict] = field(
        default_factory=list
    )  # [{data, nome, relevancia}]
    insights_concorrencia: list[dict] = field(
        default_factory=list
    )  # [{concorrente, insight}]
    conteudo_viral: list[dict] = field(
        default_factory=list
    )  # [{descricao, porque_viralizou}]
    resumo: str = ""


@dataclass
class EstrategiaResult:
    """Output of Estrategista Agent."""

    temas: list[dict] = field(default_factory=list)  # [{tema, pilar, justificativa}]
    calendario: list[dict] = field(default_factory=list)  # [{data, tipo, titulo}]
    resumo_estrategico: str = ""


@dataclass
class ConteudoGerado:
    """A single content piece."""

    tipo: str  # video_roteiro, arte_estatica, carrossel
    pilar: str
    framework: str  # AIDA, PAS, Hook-Story-Offer
    titulo: str
    conteudo: dict  # varies by type
    variacoes_ab: list[dict] = field(default_factory=list)
    referencia_visual: str = ""
    ordem: int = 0


@dataclass
class RevisaoResult:
    """Output of Revisor Agent."""

    score: int = 0  # 0-100
    aprovado: bool = False
    notas: list[str] = field(default_factory=list)
    conteudos_revisados: list[dict] = field(default_factory=list)


@dataclass
class DecisionEntry:
    agent_name: str
    timestamp: str
    decision: str
    reasoning: str


@dataclass
class PipelineContext:
    """Shared context for the planning pipeline."""

    planejamento_id: str
    cliente: ClienteData
    mes_referencia: str
    inputs_extras: str | None = None
    tipos_conteudo_override: list[dict] | None = None
    historico_temas: list[dict] = field(default_factory=list)  # last 3 months
    foco: str | None = None
    destino_conversao: str | None = None
    tipo_conteudo_uso: str | None = None
    plataformas: list[str] = field(default_factory=list)

    # Agent outputs
    pesquisa: PesquisaResult | None = None
    estrategia: EstrategiaResult | None = None
    conteudos: list[ConteudoGerado] = field(default_factory=list)
    revisao: RevisaoResult | None = None

    # Pipeline metadata
    iteration: int = 0
    max_iterations: int = 3
    decision_log: list[DecisionEntry] = field(default_factory=list)
    current_status: str = "pending"
    started_at: str | None = None
    completed_at: str | None = None

    def log_decision(self, agent_name: str, decision: str, reasoning: str):
        self.decision_log.append(
            DecisionEntry(
                agent_name=agent_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                decision=decision,
                reasoning=reasoning,
            )
        )

    def to_dict(self) -> dict:
        from dataclasses import asdict

        return asdict(self)

    @staticmethod
    def _filter_fields(cls, data: dict) -> dict:
        from dataclasses import fields as dc_fields

        valid = {f.name for f in dc_fields(cls)}
        return {k: v for k, v in data.items() if k in valid}

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineContext":
        _ff = cls._filter_fields
        data["cliente"] = ClienteData(**_ff(ClienteData, data["cliente"]))
        if data.get("pesquisa"):
            data["pesquisa"] = PesquisaResult(
                **_ff(PesquisaResult, data["pesquisa"])
            )
        if data.get("estrategia"):
            data["estrategia"] = EstrategiaResult(
                **_ff(EstrategiaResult, data["estrategia"])
            )
        data["conteudos"] = [
            ConteudoGerado(**_ff(ConteudoGerado, c))
            for c in data.get("conteudos", [])
        ]
        if data.get("revisao"):
            data["revisao"] = RevisaoResult(
                **_ff(RevisaoResult, data["revisao"])
            )
        data["decision_log"] = [
            DecisionEntry(**_ff(DecisionEntry, d))
            for d in data.get("decision_log", [])
        ]
        filtered = _ff(cls, data)
        return cls(**filtered)
