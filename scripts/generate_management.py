"""Generate typed Python bindings from the mounted public OpenAPI document."""

from __future__ import annotations

import argparse
import json
import keyword
import re
from pathlib import Path
from typing import Any

METHODS = {"get", "post", "patch", "put", "delete", "head", "options", "trace"}
HEADERS = {
    "if-match": "if_match",
    "idempotency-key": "idempotency_key",
    "confirmation-token": "confirmation_token",
    "x-stwrd-step-up": "step_up_token",
}


def identifier(value: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    value = re.sub(r"[^a-zA-Z0-9_]", "_", value).lower()
    if not value or value[0].isdigit():
        value = "value_" + value
    return value + "_" if keyword.iskeyword(value) else value


def typename(value: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in identifier(value).split("_") if part)


class Generator:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.components = document.get("components", {}).get("schemas", {})
        self.names: dict[str, str] = {}
        self.reserved: set[str] = {"ManagementClient", "ManagementOperations"}
        self.definitions: list[str] = []
        for name in sorted(self.components):
            self.names[name] = self.claim(typename(name))

    def claim(self, name: str) -> str:
        if name in self.reserved:
            raise ValueError(f"Generated name collision: {name}")
        self.reserved.add(name)
        return name

    def resolve(self, node: dict[str, Any]) -> dict[str, Any]:
        seen: set[str] = set()
        while "$ref" in node:
            ref = node["$ref"]
            if not ref.startswith("#/") or ref in seen:
                raise ValueError("Unsupported or cyclic OpenAPI reference")
            seen.add(ref)
            target: Any = self.document
            for part in ref[2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            node = target
        return node

    def object_shape(self, node: dict[str, Any]) -> dict[str, Any]:
        node = self.resolve(node)
        if "allOf" not in node:
            return node
        merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
        for branch in node["allOf"]:
            shape = self.object_shape(branch)
            if shape.get("type") != "object" and "properties" not in shape:
                raise ValueError("allOf requires object schemas")
            for key, value in shape.get("properties", {}).items():
                if key in merged["properties"] and merged["properties"][key] != value:
                    raise ValueError("Conflicting allOf property")
                merged["properties"][key] = value
            merged["required"] += shape.get("required", [])
        return merged

    def schema_type(self, node: dict[str, Any], hint: str) -> str:
        if "$ref" in node:
            prefix = "#/components/schemas/"
            if not node["$ref"].startswith(prefix):
                raise ValueError("Schema reference must address a component schema")
            return self.names[node["$ref"][len(prefix) :].replace("~1", "/").replace("~0", "~")]
        if "const" in node:
            return "None" if node["const"] is None else f"Literal[{node['const']!r}]"
        if "enum" in node:
            return (
                " | ".join(
                    "None" if value is None else f"Literal[{value!r}]" for value in node["enum"]
                )
                or "Never"
            )
        if "anyOf" in node or "oneOf" in node:
            return (
                " | ".join(
                    dict.fromkeys(
                        self.schema_type(part, hint + str(i))
                        for i, part in enumerate(node.get("anyOf", node.get("oneOf", [])))
                    )
                )
                or "Never"
            )
        if isinstance(node.get("type"), list):
            return " | ".join(
                self.schema_type({**node, "type": kind}, hint) for kind in node["type"]
            )
        kind = node.get("type")
        if kind == "array":
            return f"list[{self.schema_type(node.get('items', {}), hint + 'Item')}]"
        if kind == "object" or "properties" in node or "allOf" in node:
            shape = self.object_shape(node)
            properties = shape.get("properties", {})
            if not properties:
                extra = shape.get("additionalProperties", True)
                return (
                    "dict[str, "
                    + (
                        self.schema_type(extra, hint + "Value")
                        if isinstance(extra, dict)
                        else "Any"
                    )
                    + "]"
                )
            name = self.claim(hint)
            entries = []
            for key, value in properties.items():
                typ = self.schema_type(value, name + typename(key))
                wrapper = "Required" if key in shape.get("required", []) else "NotRequired"
                entries.append(f"{key!r}: {wrapper}[{typ!r}]")
            self.definitions.append(f"{name} = TypedDict({name!r}, {{{', '.join(entries)}}})")
            return name
        return {
            "string": "bytes" if node.get("format") == "binary" else "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "null": "None",
        }.get(kind, "Any")

    def components_code(self) -> None:
        for raw, name in self.names.items():
            node = self.components[raw]
            # Release the component's name so an object can define it directly.
            self.reserved.remove(name)
            typ = self.schema_type(node, name)
            if typ != name:
                self.claim(name)
                self.definitions.append(f"type {name} = {typ}")

    def parameters(
        self, path_item: dict[str, Any], operation: dict[str, Any]
    ) -> list[dict[str, Any]]:
        combined: dict[tuple[str, str], dict[str, Any]] = {}
        for raw in path_item.get("parameters", []) + operation.get("parameters", []):
            parameter = self.resolve(raw)
            combined[(parameter["in"], parameter["name"])] = parameter
        return list(combined.values())

    def generate(self) -> str:
        self.components_code()
        methods: list[str] = []
        groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        operation_names: set[str] = set()
        for path, raw_item in sorted(self.document.get("paths", {}).items()):
            if not path.startswith("/api/v1/"):
                raise ValueError("Only mounted public API v1 paths may be generated")
            path_item = self.resolve(raw_item)
            for verb, raw_operation in path_item.items():
                if verb not in METHODS:
                    continue
                if verb in {"trace", "options"}:
                    raise ValueError("Transport does not support this HTTP operation")
                operation = self.resolve(raw_operation)
                if not operation.get("operationId"):
                    raise ValueError("Every operation requires an operationId")
                name = identifier(operation["operationId"])
                if name in operation_names or name in {"__init__"}:
                    raise ValueError("Duplicate operation identifier")
                operation_names.add(name)
                prefix = typename(name)
                parameters = self.parameters(path_item, operation)
                paths = [p for p in parameters if p["in"] == "path"]
                queries = [p for p in parameters if p["in"] == "query"]
                placeholders = re.findall(r"\{([^}]+)\}", path)
                if set(placeholders) != {p["name"] for p in paths} or any(
                    not p.get("required") for p in paths
                ):
                    raise ValueError("Path arguments do not match mounted placeholders")
                path_args = [
                    (
                        identifier(p["name"]),
                        self.schema_type(p.get("schema", {}), prefix + typename(p["name"])),
                        p["name"],
                    )
                    for p in paths
                ]
                if len({p[0] for p in path_args}) != len(path_args) or {p[0] for p in path_args} & {
                    "body",
                    "query",
                    "options",
                    "identity",
                    "self",
                }:
                    raise ValueError("Path argument name collision")
                args = [f"{key}: {typ}" for key, typ, _ in path_args]
                call_args = [f"{key}={key}" for key, _, _ in path_args]
                query_name: str | None = None
                query_required = any(p.get("required") for p in queries)
                if queries:
                    query_name = self.schema_type(
                        {
                            "type": "object",
                            "properties": {p["name"]: p.get("schema", {}) for p in queries},
                            "required": [p["name"] for p in queries if p.get("required")],
                        },
                        prefix + "Query",
                    )
                    args.append(
                        f"query: {query_name}"
                        if query_required
                        else f"query: {query_name} | None = None"
                    )
                    call_args.append("query=query")
                required_headers = []
                for p in parameters:
                    if p["in"] == "header" and p.get("required"):
                        if p["name"].lower() not in HEADERS:
                            raise ValueError("Unsupported required request header")
                        required_headers.append(HEADERS[p["name"].lower()])
                    elif p["in"] not in {"path", "query", "header"}:
                        raise ValueError("Unsupported operation parameter")
                options_type = "WriteOptions"
                if required_headers:
                    options_type = self.claim(prefix + "WriteOptions")
                    self.definitions.append(
                        "@dataclass(frozen=True, kw_only=True)\nclass "
                        + options_type
                        + "(WriteOptions):\n"
                        + "\n".join(f"    {header}: str = field()" for header in required_headers)
                    )
                args.append(
                    f"options: {options_type}"
                    if required_headers
                    else "options: WriteOptions | None = None"
                )
                call_args.append("options=options")
                body_expr = "None"
                request_body = (
                    self.resolve(operation["requestBody"]) if "requestBody" in operation else None
                )
                if request_body:
                    content = request_body.get("content", {})
                    if "application/json" in content:
                        body_type = self.schema_type(
                            content["application/json"].get("schema", {}), prefix + "Body"
                        )
                    elif "multipart/form-data" in content:
                        body_type = "MultipartInput"
                        # Export the schema; multipart uses the transport's file wrapper.
                        self.schema_type(
                            content["multipart/form-data"].get("schema", {}),
                            prefix + "MultipartSchema",
                        )
                    else:
                        raise ValueError("Unsupported request body media type")
                    args.append(
                        f"body: {body_type}"
                        if request_body.get("required")
                        else f"body: {body_type} | None = None"
                    )
                    call_args.append("body=body")
                    body_expr = "body"
                response_types: list[str] = []
                page_items: list[dict[str, Any]] = []
                binary = True
                for status, raw_response in operation.get("responses", {}).items():
                    if not re.fullmatch(r"2\d\d", status):
                        continue
                    response = self.resolve(raw_response)
                    content = response.get("content", {})
                    if not content or verb == "head":
                        response_types.append("None")
                    elif "application/json" in content:
                        binary = False
                        schema = content["application/json"].get("schema", {})
                        response_types.append(
                            self.schema_type(schema, prefix + "Response" + status)
                        )
                        shape = self.object_shape(schema)
                        properties = shape.get("properties", {})
                        if "items" in properties and "page" in properties:
                            items = self.resolve(properties["items"])
                            page = self.object_shape(properties["page"])
                            if items.get("type") == "array" and "next_cursor" in page.get(
                                "properties", {}
                            ):
                                page_items.append(items.get("items", {}))
                    else:
                        response_types.append("bytes")
                if not response_types:
                    raise ValueError("Operation has no successful response")
                result_type = " | ".join(dict.fromkeys(response_types))
                relative = path[len("/api/v1") :]
                parts = []
                for segment in relative.split("/"):
                    match = re.fullmatch(r"\{([^}]+)\}", segment)
                    parts.append(
                        f"quote(str({identifier(match[1])}), safe='')" if match else repr(segment)
                    )
                path_expr = " + '/' + ".join(parts)
                options_expr = "options or WriteOptions()"
                if binary and "bytes" in response_types:
                    options_expr = f"replace({options_expr}, response_type='bytes')"
                query_expr = (
                    "cast(Mapping[str, QueryValue], query) if query is not None else None"
                    if queries
                    else "None"
                )
                methods.append(
                    f"    async def {name}(self, *, {', '.join(args)}) -> ApiResult[{result_type}]:\n        return cast(ApiResult[{result_type}], await self._transport.request({verb.upper()!r}, {path_expr}, {body_expr}, {options_expr}, {query_expr}))"  # noqa: E501 -- emitted source template
                )
                segments = tuple(
                    identifier(part)
                    for part in relative.strip("/").split("/")
                    if not part.startswith("{")
                )
                convenience = {
                    "get": "list" if page_items else "get",
                    "post": "create",
                    "patch": "update",
                    "put": "replace",
                    "delete": "delete",
                    "head": "head",
                }[verb]
                group = {
                    "name": name,
                    "args": args,
                    "calls": call_args,
                    "result": result_type,
                    "method": convenience,
                    "path_args": path_args,
                    "query_name": query_name,
                    "query_required": query_required,
                    "path_expr": path_expr,
                }
                groups.setdefault(segments, []).append(group)
                if verb == "get" and page_items:
                    if any(item != page_items[0] for item in page_items):
                        raise ValueError("Paged success responses disagree on item schema")
                    item_type = self.schema_type(page_items[0], prefix + "IteratorItem")
                    item_shape = self.object_shape(page_items[0])
                    has_id = "id" in item_shape.get("required", []) and "id" in item_shape.get(
                        "properties", {}
                    )
                    iterator_args = [f"{key}: {typ}" for key, typ, _ in path_args]
                    if queries:
                        iterator_args.append(
                            f"query: {query_name}"
                            if query_required
                            else f"query: {query_name} | None = None"
                        )
                    iterator_args.append(
                        f"identity: Callable[[{item_type}], str | int]"
                        + (" | None = None" if has_id else "")
                    )
                    default_identity = (
                        "identity or (lambda item: cast(str | int, item['id']))"
                        if has_id
                        else "identity"
                    )
                    iterator_query = "cast(Mapping[str, QueryValue], query)" if queries else "None"
                    methods.append(
                        f"    def {name}_iterate(self, *, {', '.join(iterator_args)}) -> AsyncIterator[{item_type}]:\n        return self._transport.iterate({path_expr}, {iterator_query}, identity={default_identity})"  # noqa: E501 -- emitted source template
                    )
                    group["iterator"] = {
                        "args": iterator_args,
                        "type": item_type,
                        "calls": [f"{key}={key}" for key, _, _ in path_args]
                        + (["query=query"] if queries else [])
                        + ["identity=identity"],
                    }
        group_code: list[str] = []
        all_groups = set(groups)
        for group in list(all_groups):
            all_groups.update(group[:i] for i in range(1, len(group)))
        for group in sorted(all_groups, key=lambda item: (-len(item), item)):
            class_name = self.claim("Resource" + "".join(typename(part) for part in group))
            children = sorted(
                item for item in all_groups if len(item) == len(group) + 1 and item[:-1] == group
            )
            entries = groups.get(group, [])
            names = [entry["method"] for entry in entries]
            if len(set(names)) != len(names) or set(names) & {child[-1] for child in children}:
                raise ValueError("Convenience group name collision")
            init = ["        self._operations = operations"] + [
                f"        self.{child[-1]} = Resource{''.join(typename(part) for part in child)}(operations)"  # noqa: E501 -- emitted source template
                for child in children
            ]
            lines = [
                f"class {class_name}:",
                "    def __init__(self, operations: ManagementOperations) -> None:",
                *init,
            ]
            for entry in entries:
                lines.append(
                    f"    async def {entry['method']}(self, *, {', '.join(entry['args'])}) -> ApiResult[{entry['result']}]:\n        return await self._operations.{entry['name']}({', '.join(entry['calls'])})"  # noqa: E501 -- emitted source template
                )
                if "iterator" in entry:
                    iterator = entry["iterator"]
                    lines.append(
                        f"    def iterate(self, *, {', '.join(iterator['args'])}) -> AsyncIterator[{iterator['type']}]:\n        return self._operations.{entry['name']}_iterate({', '.join(iterator['calls'])})"  # noqa: E501 -- emitted source template
                    )
            group_code.append("\n".join(lines))
        root = [
            "class ManagementClient(ManagementTransport):",
            "    def __init__(self, options: ManagementOptions, *, http_client: httpx.AsyncClient | None = None) -> None:",  # noqa: E501 -- emitted source template
            "        super().__init__(options, http_client=http_client)",
            "        self.operations = ManagementOperations(self)",
        ]
        root += [
            f"        self.{group[0]} = Resource{typename(group[0])}(self.operations)"
            for group in sorted(all_groups)
            if len(group) == 1
        ]
        return "\n\n".join(
            [
                '"""Generated from the mounted public OpenAPI document. Do not edit."""\nfrom __future__ import annotations\nfrom collections.abc import AsyncIterator, Callable, Mapping\nfrom dataclasses import dataclass, field, replace\nfrom typing import Any, Literal, Never, NotRequired, Required, TypedDict, cast\nfrom urllib.parse import quote\nimport httpx\nfrom .management import ApiResult, ManagementOptions, ManagementTransport, MultipartInput, QueryValue, WriteOptions',  # noqa: E501 -- emitted source template
                *self.definitions,
                "class ManagementOperations:\n    def __init__(self, transport: ManagementTransport) -> None:\n        self._transport = transport\n"  # noqa: E501 -- emitted source template
                + "\n\n".join(methods),
                *group_code,
                "\n".join(root),
                "def create_management(options: ManagementOptions, *, http_client: httpx.AsyncClient | None = None) -> ManagementClient:\n    return ManagementClient(options, http_client=http_client)",  # noqa: E501 -- emitted source template
                "",
            ]
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    document = json.loads(args.schema.read_text())
    result = Generator(document).generate()
    args.output.write_text(result)


if __name__ == "__main__":
    main()
