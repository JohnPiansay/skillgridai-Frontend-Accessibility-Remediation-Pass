#!/usr/bin/env python3
"""Find common accessibility issues in static HTML files.

This is a lightweight static check, not a substitute for keyboard, screen-reader,
or browser-based accessibility testing.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    rule: str
    message: str
    suggestion: str


@dataclass
class Element:
    tag: str
    attributes: Dict[str, Optional[str]]
    line: int
    text: str = ""
    wrapped_by_label: bool = False


VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

FORM_CONTROLS = {"input", "select", "textarea"}
SKIP_FORM_LABEL_TYPES = {"hidden", "button", "submit", "reset"}


class AccessibilityParser(HTMLParser):
    """Collect simple, source-level accessibility findings from one HTML file."""

    def __init__(self, filename: str) -> None:
        super().__init__(convert_charrefs=True)
        self.filename = filename
        self.findings: List[Finding] = []
        self.elements: List[Element] = []
        self.stack: List[int] = []
        self.labelled_ids: Set[str] = set()
        self.html_has_lang = False
        self.previous_heading_level: Optional[int] = None

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        self._handle_element(tag, attrs, push=tag not in VOID_ELEMENTS)

    def handle_startendtag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        self._handle_element(tag, attrs, push=False)

    def _handle_element(
        self,
        tag: str,
        attrs: List[Tuple[str, Optional[str]]],
        *,
        push: bool,
    ) -> None:
        tag = tag.lower()
        attributes = {
            name.lower(): value
            for name, value in attrs
        }
        element = Element(
            tag=tag,
            attributes=attributes,
            line=self.getpos()[0],
            wrapped_by_label=any(
                self.elements[index].tag == "label"
                for index in self.stack
            ),
        )
        index = len(self.elements)
        self.elements.append(element)

        if tag == "html" and attributes.get("lang", "").strip():
            self.html_has_lang = True
        elif tag == "label":
            target_id = attributes.get("for")
            if target_id:
                self.labelled_ids.add(target_id)

        if push:
            self.stack.append(index)

        if tag == "img":
            self._check_image(element)
            self._append_to_ancestors(attributes.get("alt") or "")
        elif tag == "input":
            self._check_input(element)
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._check_heading(tag, element.line)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for position in range(len(self.stack) - 1, -1, -1):
            if self.elements[self.stack[position]].tag == tag:
                del self.stack[position:]
                return

    def handle_data(self, data: str) -> None:
        self._append_to_ancestors(data)

    def _append_to_ancestors(self, text: str) -> None:
        if text:
            for index in self.stack:
                self.elements[index].text += text

    def _add_finding(
        self,
        element: Element,
        rule: str,
        message: str,
        suggestion: str,
    ) -> None:
        self.findings.append(
            Finding(self.filename, element.line, rule, message, suggestion)
        )

    @staticmethod
    def _has_aria_name(element: Element) -> bool:
        return any(
            element.attributes.get(attribute, "").strip()
            for attribute in ("aria-label", "aria-labelledby")
        )

    def _check_image(self, element: Element) -> None:
        if "alt" not in element.attributes:
            self._add_finding(
                element,
                "IMG001",
                "Image is missing an alt attribute.",
                "Add descriptive alt text, or alt=\"\" when the image is decorative.",
            )

    def _check_named_element(
        self, element: Element, rule: str, role: str
    ) -> None:
        if self._has_aria_name(element):
            return
        if element.text.strip():
            return
        self._add_finding(
            element,
            rule,
            f"{role.capitalize()} has no detectable accessible name.",
            f"Add meaningful text or an appropriate aria-label to the {role}.",
        )

    def _check_input(self, element: Element) -> None:
        input_type = (element.attributes.get("type") or "text").lower()
        if input_type == "image":
            if not (element.attributes.get("alt") or "").strip():
                self._add_finding(
                    element,
                    "IMG002",
                    "Image input is missing descriptive alt text.",
                    "Add an alt attribute that describes the input's action.",
                )
            return

        if input_type in SKIP_FORM_LABEL_TYPES:
            if input_type in {"button", "submit", "reset"} and not (
                (element.attributes.get("value") or "").strip()
                or self._has_aria_name(element)
            ):
                self._add_finding(
                    element,
                    "BUTTON001",
                    "Button input has no detectable accessible name.",
                    "Add a descriptive value or an appropriate aria-label.",
                )
            return

    def _check_heading(self, tag: str, line: int) -> None:
        level = int(tag[1])
        if (
            self.previous_heading_level is not None
            and level > self.previous_heading_level + 1
        ):
            self.findings.append(
                Finding(
                    self.filename,
                    line,
                    "HEADING001",
                    f"Heading level jumps from h{self.previous_heading_level} to {tag}.",
                    "Use the next heading level in sequence, or restructure the headings.",
                )
            )
        self.previous_heading_level = level

    def finish(self) -> List[Finding]:
        if not self.html_has_lang:
            self.findings.append(
                Finding(
                    self.filename,
                    1,
                    "HTML001",
                    "Root <html> element has no language declaration.",
                    'Add a valid language tag, for example <html lang="en">.',
                )
            )

        for element in self.elements:
            if element.tag in {"a", "button"}:
                self._check_named_element(
                    element,
                    "LINK001" if element.tag == "a" else "BUTTON001",
                    "link" if element.tag == "a" else "button",
                )
            if element.tag in FORM_CONTROLS and (
                element.tag != "input"
                or (element.attributes.get("type") or "text").lower()
                not in SKIP_FORM_LABEL_TYPES
            ):
                control_id = element.attributes.get("id")
                labelled = (
                    element.wrapped_by_label
                    or (control_id is not None and control_id in self.labelled_ids)
                    or self._has_aria_name(element)
                )
                if not labelled:
                    self._add_finding(
                        element,
                        "FORM001",
                        f"{element.tag.capitalize()} has no detectable accessible label.",
                        "Add a matching <label>, aria-label, or aria-labelledby attribute.",
                    )

        return self.findings


def audit_file(path: Path) -> List[Finding]:
    source = path.read_text(encoding="utf-8")
    parser = AccessibilityParser(str(path))
    parser.feed(source)
    parser.close()
    return parser.finish()


def collect_html_files(paths: Sequence[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if path.is_dir():
            files.extend(
                child
                for child in path.rglob("*")
                if child.is_file() and child.suffix.lower() in {".html", ".htm"}
            )
        elif path.suffix.lower() in {".html", ".htm"}:
            files.append(path)
        else:
            raise ValueError(f"Expected an HTML file or directory: {path}")
    return sorted(set(files))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check HTML files for common accessibility issues."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="HTML files or directories to scan recursively",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="exit with status 1 when findings are reported",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        files = collect_html_files(args.paths)
        findings = [
            finding
            for path in files
            for finding in audit_file(path)
        ]
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))

    if args.format == "json":
        print(json.dumps([asdict(finding) for finding in findings], indent=2))
    elif findings:
        for finding in findings:
            print(
                f"{finding.file}:{finding.line}: "
                f"{finding.rule} {finding.message}\n"
                f"  Suggestion: {finding.suggestion}"
            )
        print(f"\n{len(findings)} finding(s) in {len(files)} HTML file(s).")
    else:
        print(f"No findings in {len(files)} HTML file(s).")

    return 1 if findings and args.fail_on_issues else 0


if __name__ == "__main__":
    sys.exit(main())
