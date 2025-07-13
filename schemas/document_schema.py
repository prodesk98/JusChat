from typing import Optional

from pydantic import BaseModel, Field


class LegalDocumentMetadata(BaseModel):
    # Document Identification
    title: Optional[str] = Field(None, description="Title of the legal document")
    type: Optional[str] = Field(None, description="Type of the legal document")
    case_number: Optional[str] = Field(None, description="Official case number")
    document_number: Optional[str] = Field(None, description="Internal document number")
    creation_date: Optional[str] = Field(None, description="Date when the document was created")
    filing_date: Optional[str] = Field(None, description="Date when the document was filed")
    signature_date: Optional[str] = Field(None, description="Date when the document was signed")
    version: Optional[str] = Field(None, description="Version or revision of the document")
    place_of_issue: Optional[str] = Field(None, description="Place where the document was issued")

    # Parties Involved
    plaintiffs: Optional[list[str]] = Field(None, description="List of plaintiffs")
    defendants: Optional[list[str]] = Field(None, description="List of defendants")
    lawyers: Optional[list[str]] = Field(None, description="List of lawyers involved")
    bar_number: Optional[list[str]] = Field(None, description="List of bar registration numbers")
    legal_representatives: Optional[list[str]] = Field(None, description="Other legal representatives")
    judge_or_rapporteur: Optional[str] = Field(None, description="Name of judge or rapporteur")
    third_parties: Optional[list[str]] = Field(None, description="Interested third parties")

    # Procedural Data
    court: Optional[str] = Field(None, description="Court where the case is processed")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction")
    district: Optional[str] = Field(None, description="Judicial district")
    adjudicating_body: Optional[str] = Field(None, description="Adjudicating body or chamber")
    case_class: Optional[str] = Field(None, description="Class of the legal action")
    nature_of_action: Optional[str] = Field(None, description="Nature of the action")
    main_subject: Optional[str] = Field(None, description="Main subject of the action")
    secondary_subjects: Optional[list[str]] = Field(None, description="Other related subjects")
    case_progress: Optional[str] = Field(None, description="Current case progress stage")
    case_stage: Optional[str] = Field(None, description="Current stage in process")

    # Legal Information
    legal_basis: Optional[list[str]] = Field(None, description="Articles, laws or norms cited")
    jurisprudence: Optional[list[str]] = Field(None, description="Precedents or case law cited")
    legal_thesis: Optional[str] = Field(None, description="Legal thesis argued")
    claims: Optional[list[str]] = Field(None, description="Claims requested")
    legal_reasoning: Optional[str] = Field(None, description="Legal reasoning or justification")
    provisions: Optional[list[str]] = Field(None, description="Provisions applied")
    decision: Optional[str] = Field(None, description="Decision content")
    case_value: Optional[str] = Field(None, description="Value attributed to the case")
    attorney_fees: Optional[str] = Field(None, description="Agreed or court-appointed attorney fees")
