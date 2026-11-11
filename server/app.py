"""Local-only API and production SPA server. Python 3.10+, standard library only."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import secrets
from urllib.parse import urlsplit, unquote

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server.domain import CourseImport, ValidationError
from server.repository import CourseRepository

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 2 * 1024 * 1024


def handler_for(repository, dist=ROOT / 'dist'):
    connector_key = secrets.token_hex(16)
    class Handler(BaseHTTPRequestHandler):
        server_version = 'KejiLocal/0.2'

        def json_response(self, status, data):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/api/health':
                return self.json_response(200, {'status': 'ok', 'mode': 'local-single-user'})
            if path.startswith('/api/') and self.headers.get('Host','') not in {f'{h}:{self.server.server_port}' for h in ('127.0.0.1','localhost')}:
                return self.json_response(403, {'error':'只允许本机域名访问'})
            if path == '/api/connector':
                origin = self.headers.get('Origin')
                if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}', 'http://127.0.0.1:5173', f'http://localhost:{self.server.server_port}', 'http://localhost:5173'}:
                    return self.json_response(403, {'error':'连接码只能在本机课迹页面查看'})
                return self.json_response(200, {'pairingCode':connector_key})
            if path == '/api/catalog':
                return self.json_response(200, repository.catalog())
            match = re.fullmatch(r'/api/records/([a-f0-9]{24})/history', path)
            if match:
                return self.json_response(200, {'versions': repository.history(match[1])})
            if path.startswith('/api/'):
                return self.json_response(404, {'error': '接口不存在'})
            target = (dist / unquote(path).lstrip('/')).resolve()
            if not target.is_relative_to(dist.resolve()):
                return self.json_response(404, {'error': '文件不存在'})
            if not target.is_file():
                if '.' in Path(path).name:
                    return self.json_response(404, {'error': '文件不存在'})
                target = dist / 'index.html'
            if not target.is_file():
                return self.json_response(503, {'error': '尚未构建前端，请先运行 npm run build；开发时打开5173端口'})
            body = target.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def read_body(self, extension=False):
            # JSON-only writes plus exact loopback origins prevent cross-site form writes.
            allowed = {f'http://{host}:{port}' for host in ('localhost', '127.0.0.1')
                       for port in (5173, self.server.server_port)}
            host = self.headers.get('Host', '')
            if host not in {f'{h}:{self.server.server_port}' for h in ('localhost', '127.0.0.1')}:
                raise ValidationError('只允许本机访问')
            origin = self.headers.get('Origin')
            if extension:
                key = self.headers.get('X-Keji-Key', '')
                if not secrets.compare_digest(key, connector_key):
                    raise ValidationError('连接码无效，请从当前课迹页面重新复制')
            if not extension and origin and origin not in allowed:
                raise ValidationError('不允许此来源写入')
            if self.headers.get_content_type() != 'application/json':
                raise ValidationError('请使用 application/json')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= MAX_BODY:
                    raise ValueError()
                return json.loads(self.rfile.read(length).decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                raise ValidationError('JSON格式无效或文件超过2MB')

        def do_POST(self):
            try:
                endpoint = urlsplit(self.path).path
                if endpoint not in ('/api/imports','/api/blackboard/imports'):
                    return self.json_response(404, {'error': '接口不存在'})
                body = self.read_body(extension=endpoint == '/api/blackboard/imports')
                if endpoint == '/api/blackboard/imports':
                    from server.blackboard import validate_collection
                    validate_collection(body)
                bundle = CourseImport.parse(body)
                return self.json_response(200, repository.save_import(bundle))
            except ValidationError as error:
                return self.json_response(400, {'error': str(error)})
            except Exception:
                return self.json_response(500, {'error': '保存失败，本次导入未完成，请稍后重试'})

        def do_PATCH(self):
            try:
                match = re.fullmatch(r'/api/deadlines/([a-f0-9]{24})', urlsplit(self.path).path)
                if not match:
                    return self.json_response(404, {'error': '接口不存在'})
                body = self.read_body()
                if not isinstance(body, dict) or type(body.get('done')) is not bool:
                    raise ValidationError('done 必须是布尔值')
                return self.json_response(200, repository.set_done(match[1], body['done']))
            except ValidationError as error:
                return self.json_response(400, {'error': str(error)})
            except KeyError:
                return self.json_response(404, {'error': '截止项不存在'})
            except Exception:
                return self.json_response(500, {'error': '状态保存失败，请稍后重试'})

        def log_message(self, format, *args):
            # Never log request bodies or imported course content.
            pass
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--db', default=str(ROOT / '.local-data' / 'courses.sqlite3'))
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(CourseRepository(args.db)))
    print(f'课迹本地服务：http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
