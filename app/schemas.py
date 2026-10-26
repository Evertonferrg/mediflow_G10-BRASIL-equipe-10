from typing import Optional, List
from pydantic import BaseModel, Field

class Paciente(BaseModel):
    nome: Optional[str] = None
    idade: Optional[int] = None

class Medico(BaseModel): 
    nome: Optional[str] = None
    crm: Optional[str] = None

class Extracao(BaseModel):
    tipo_documento: str
    nivel_prioridade: str
    score_confianca_classificacao: float = Field(ge=0, le=1)
    paciente: Paciente = Paciente()
    medico_solicitante: Medico = Medico()
    diagnostico_principal: Optional[str] = None
    medicamentos: List[str] = []
    inconsistencias: List[str] = []