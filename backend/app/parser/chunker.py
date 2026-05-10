import yaml
import json
from typing import List, Dict, Any

class OpenAPIChunker:
    """
    OpenAPI/Swagger 文档分片器。

    支持 JSON 与 YAML 格式，按 ``path + method`` 为最小单元拆分文档，
    并递归展开 ``$ref`` 引用，生成适合 Embedding 的文本块。
    """

    def parse(self, content: bytes, filename: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        解析文档内容并生成 Chunk 列表。

        Args:
            content: 文档原始字节内容。
            filename: 原始文件名（用于判断 JSON/YAML）。
            doc_id: 文档唯一标识（会写入 chunk metadata）。

        Returns:
            Chunk 字典列表，每条包含 ``id``、``text``、``metadata``。
        """
        if filename.endswith('.json'):
            spec = json.loads(content.decode('utf-8'))
        else:
            spec = yaml.safe_load(content.decode('utf-8'))
        
        paths = spec.get('paths', {})
        schemas = spec.get('components', {}).get('schemas', {})
        chunks = []

        for path, methods in paths.items():
            for method, operation in methods.items():
                if not isinstance(operation, dict):
                    continue
                path_clean = path.replace('/', '_').replace('{', '').replace('}', '')
                chunk_id = f"ep_{len(chunks)}_{method}_{path_clean}_{doc_id}"
                text = self._build_chunk_text(path, method, operation, schemas)
                tags = operation.get('tags', [])
                metadata = {
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get('summary', ''),
                    "tags": ",".join(tags) if tags else "",
                    "doc_id": doc_id,
                }
                chunks.append({"id": chunk_id, "text": text, "metadata": metadata})
        return chunks
    
    def _build_chunk_text(self, path, method, operation, schemas):
        """
        为单个端点构建可读的文本描述。

        Args:
            path: API 路径。
            method: HTTP 方法。
            operation: OpenAPI Operation 对象。
            schemas: 全局 Schema 定义，用于展开 ``$ref``。

        Returns:
            拼接好的多行文本字符串。
        """
        lines = [f"API Endpoint: {method.upper()} {path}"]
        if operation.get('summary'):
            lines.append(f"Summary: {operation['summary']}")
        if operation.get('description'):
            lines.append(f"Description: {operation['description']}")
        
        for param in operation.get('parameters', []):
            if isinstance(param, dict):
                lines.append(
                    f"  - {param.get('name')} ({param.get('in')}, "
                    f"{param.get('schema', {}).get('type', 'unknown')}): "
                    f"{param.get('description', '')}"
                )
        
        request_body = operation.get('requestBody', {})
        if request_body:
            for media_type, media_obj in request_body.get('content', {}).items():
                lines.append(f"Request Body ({media_type}):")
                lines.extend(self._describe_schema(media_obj.get("schema", {}), schemas, indent=2))
        
        for status in ["200", "201"]:
            if status in operation.get("responses", {}):
                resp = operation["responses"][status]
                lines.append(f"Response {status}: {resp.get('description', '')}")
                for media_type, media_obj in resp.get("content", {}).items():
                    lines.append(f" Response Body ({media_type}):")
                    lines.extend(self._describe_schema(media_obj.get("schema", {}), schemas, indent=4))
                break
        return '\n'.join(lines)

    def _describe_schema(self, schema, schemas, indent=0):
        """
        递归描述 Schema 结构（支持 ``$ref`` 展开）。

        Args:
            schema: 当前 Schema 对象或引用。
            schemas: 全局 Schema 定义字典。
            indent: 当前缩进空格数。

        Returns:
            描述该 Schema 的多行文本列表。
        """
        lines = []
        prefix = "  " * indent
        ref = schema.get("$ref")
        if ref and isinstance(ref, str):
            ref_name = ref.split("/")[-1]
            if ref_name in schemas:
                lines.extend(self._describe_schema(schemas[ref_name], schemas, indent))
            else:
                lines.append(f"{prefix}Reference: {ref_name}")
            return lines
        
        schema_type = schema.get("type", "object")
        if schema_type == "object":
            for prop_name, prop_schema in schema.get("properties", {}).items():
                prop_type = prop_schema.get("type", "unknown")
                lines.append(f"{prefix}- {prop_name} ({prop_type}): {prop_schema.get('description', '')}")
                if prop_type == "object" or "$ref" in prop_schema:
                    lines.extend(self._describe_schema(prop_schema, schemas, indent + 2))
        elif schema_type == "array":
            lines.append(f"{prefix}Array items:")
            lines.extend(self._describe_schema(schema.get("items", {}), schemas, indent + 2))
        else:
            lines.append(f"{prefix}Type: {schema_type}")
        return lines
