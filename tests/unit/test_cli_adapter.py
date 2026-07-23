import argparse

from pydantic import BaseModel, Field

from bounded.adapters.cli import add_capability_subcommand, run_from_namespace
from bounded.capability import Capability


class EchoInput(BaseModel):
    text: str = Field(..., description="text to echo")
    shout: bool = Field(False, description="uppercase the output")


class EchoOutput(BaseModel):
    result: str


def _echo(input_value: EchoInput) -> EchoOutput:
    text = input_value.text.upper() if input_value.shout else input_value.text
    return EchoOutput(result=text)


echo_capability = Capability(
    name="echo",
    description="echo text back",
    input_model=EchoInput,
    output_model=EchoOutput,
    run=_echo,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_capability_subcommand(subparsers, echo_capability)
    return parser


def test_required_field_becomes_required_flag():
    parser = _build_parser()
    namespace = parser.parse_args(["echo", "--text", "hi"])
    assert namespace.text == "hi"
    assert namespace.shout is False


def test_run_from_namespace_executes_the_capability():
    parser = _build_parser()
    namespace = parser.parse_args(["echo", "--text", "hi", "--shout", "True"])
    result = run_from_namespace(echo_capability, namespace)
    assert isinstance(result, EchoOutput)
    assert result.result == "HI"
