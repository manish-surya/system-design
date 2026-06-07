"""Pydantic models for Repository Discovery output."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field


class Language(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    RUST = "rust"
    KOTLIN = "kotlin"
    PHP = "php"
    RUBY = "ruby"
    UNKNOWN = "unknown"


class Framework(str, Enum):
    # Python
    FASTAPI = "fastapi"
    DJANGO = "django"
    FLASK = "flask"
    # JS/TS
    NEXTJS = "nextjs"
    REACT = "react"
    ANGULAR = "angular"
    VUE = "vue"
    EXPRESS = "express"
    NESTJS = "nestjs"
    # Java
    SPRING = "spring"
    # Go
    GIN = "gin"
    ECHO = "echo"
    FIBER = "fiber"
    # Infra
    UNKNOWN = "unknown"


class PackageManager(str, Enum):
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    POETRY = "poetry"
    PDM = "pdm"
    CARGO = "cargo"
    GO_MOD = "go_mod"
    MAVEN = "maven"
    GRADLE = "gradle"
    BUNDLER = "bundler"


class InfrastructureType(str, Enum):
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    HELM = "helm"
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    CIRCLE_CI = "circle_ci"


class DocumentationType(str, Enum):
    README = "readme"
    OPENAPI = "openapi"
    ASYNCAPI = "asyncapi"
    ADR = "adr"
    ARCHITECTURE_DOC = "architecture_doc"
    WIKI = "wiki"


class LanguageStats(BaseModel):
    language: Language
    file_count: int
    extensions: list[str]


class FrameworkDetection(BaseModel):
    framework: Framework
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class PackageManagerDetection(BaseModel):
    manager: PackageManager
    manifest_file: str
    dependencies: list[str] = Field(default_factory=list)


class InfrastructureDetection(BaseModel):
    type: InfrastructureType
    files: list[str] = Field(default_factory=list)


class DocumentationDetection(BaseModel):
    type: DocumentationType
    path: str


class RepositoryInventory(BaseModel):
    """Complete output of Repository Discovery (Milestone 1)."""

    repository_path: str
    repository_name: str

    # Languages
    languages: list[LanguageStats] = Field(default_factory=list)
    primary_language: Language = Language.UNKNOWN

    # Frameworks
    frameworks: list[FrameworkDetection] = Field(default_factory=list)

    # Package managers
    package_managers: list[PackageManagerDetection] = Field(default_factory=list)

    # Infrastructure
    infrastructure: list[InfrastructureDetection] = Field(default_factory=list)

    # Documentation
    documentation: list[DocumentationDetection] = Field(default_factory=list)

    # Summary stats
    total_files: int = 0
    total_directories: int = 0
    has_tests: bool = False
    has_ci: bool = False

    model_config = ConfigDict(use_enum_values=True)
