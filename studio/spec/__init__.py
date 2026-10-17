"""The Business Specification: schema, loader, validation suite, compiler."""

from studio.spec.compile import COMPILER_VERSION, CompiledSpecification, compile_specification
from studio.spec.findings import Finding, SpecificationError
from studio.spec.loader import LoadedSpecification, load_specification
from studio.spec.validate import ValidationReport, validate

__all__ = [
    "COMPILER_VERSION", "CompiledSpecification", "Finding", "LoadedSpecification", "SpecificationError",
    "ValidationReport", "compile_specification", "load_specification", "validate",
]
