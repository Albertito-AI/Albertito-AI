"""Release boundary and extracted-package checks for the IBOL MCP bundle."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import package_mcpb
import publish_mcpb_release
import check_registry


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()

    def test_build_is_deterministic_and_distribution_is_scoped(self):
        first=package_mcpb.build(self.root/'one');second=package_mcpb.build(self.root/'two')
        self.assertEqual(first['bundle_sha256'],second['bundle_sha256'])
        self.assertEqual((self.root/'one'/first['filename']).read_bytes(),(self.root/'two'/second['filename']).read_bytes())
        with zipfile.ZipFile(self.root/'one'/first['filename']) as archive:
            names=set(archive.namelist())
            self.assertEqual(names,set(package_mcpb.SOURCES))
            self.assertIn('uv.lock',names);self.assertIn('RIGHTS.md',names)
            self.assertFalse(any(n.endswith('.pdf') or '.venv' in n or 'cache' in n for n in names))
            manifest=json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['server']['type'],'uv')
            self.assertIn('--frozen',manifest['server']['mcp_config']['args'])
            self.assertEqual(manifest['license'],'MIT AND CC-BY-4.0')
        server=json.loads((self.root/'one/server.json').read_text())
        self.assertEqual(server['packages'][0]['fileSha256'],first['bundle_sha256'])
        self.assertTrue(server['packages'][0]['identifier'].endswith(first['filename']))

    def test_modified_source_rejects_release_request(self):
        for source in [*package_mcpb.SOURCES.values(),'scripts/ibol/package_mcpb.py','scripts/ibol/publish_mcpb_release.py','scripts/ibol/check_registry.py','.github/workflows/ibol-registry.yml','mcp/ibol/release-request.json']:
            dest=self.root/source;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(package_mcpb.ROOT/source,dest)
        package_mcpb.validate_request(self.root)
        with (self.root/'scripts/ibol/catalog.py').open('a') as f:f.write('\n# Changed after review\n')
        with self.assertRaisesRegex(ValueError,'source digest'):
            package_mcpb.validate_request(self.root)

    def test_extracted_bundle_cli_and_actual_stdio(self):
        import subprocess
        from mcp import ClientSession,StdioServerParameters
        from mcp.client.stdio import stdio_client
        result=package_mcpb.build(self.root/'build')
        with zipfile.ZipFile(self.root/'build'/result['filename']) as archive:
            archive.extractall(self.root/'extracted')
        extracted=self.root/'extracted'
        result=subprocess.run([sys.executable,str(extracted/'scripts/cli.py'),'lesson','6'],cwd=self.root,capture_output=True,text=True,check=True)
        self.assertEqual(json.loads(result.stdout)['source_locator']['chapter'],6)
        async def scenario():
            params=StdioServerParameters(command=sys.executable,args=[str(extracted/'scripts/mcp_server.py')],env={'IBOL_CACHE_DIR':str(self.root/'absent-cache')})
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as client:
                    await client.initialize()
                    self.assertEqual(len((await client.list_tools()).tools),6)
                    citation=await client.call_tool('get_citation',{'style':'csl'})
                    self.assertFalse(citation.isError)
                    self.assertEqual((citation.structuredContent or json.loads(citation.content[0].text))['citation']['DOI'],'10.21827/6ac3948159a9e')
                    search=await client.call_tool('search_book_text',{'query':'policy'})
                    self.assertFalse((search.structuredContent or json.loads(search.content[0].text))['available'])
        asyncio.run(scenario())

    @unittest.skipUnless(shutil.which('uv'),'UV is not installed; the publication workflow requires it')
    def test_manifest_uv_launch_uses_frozen_runtime(self):
        from mcp import ClientSession,StdioServerParameters
        from mcp.client.stdio import stdio_client
        receipt=package_mcpb.build(self.root/'build')
        with zipfile.ZipFile(self.root/'build'/receipt['filename']) as archive:
            archive.extractall(self.root/'bundle')
        bundle=self.root/'bundle'
        manifest=json.loads((bundle/'manifest.json').read_text())
        args=[arg.replace('${__dirname}',str(bundle)) for arg in manifest['server']['mcp_config']['args']]
        async def scenario():
            params=StdioServerParameters(command=shutil.which('uv'),args=args,env={'IBOL_CACHE_DIR':str(self.root/'no-cache')})
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as client:
                    await client.initialize()
                    self.assertEqual(len((await client.list_tools()).tools),6)
                    result=await client.call_tool('get_practice_questions',{'chapter':1,'limit':1})
                    value=result.structuredContent or json.loads(result.content[0].text)
                    self.assertNotIn('answer',value['questions'][0])
        asyncio.run(scenario())

    def test_release_rejects_wrong_repository_and_revision_before_network(self):
        receipt=package_mcpb.build(self.root)
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':'someone/else','GITHUB_REF':'refs/heads/main'}),patch.object(publish_mcpb_release,'api') as request:
            with self.assertRaisesRegex(ValueError,'owner repository'):publish_mcpb_release.main(self.root)
            request.assert_not_called()
        with patch.dict(os.environ,{'GITHUB_REPOSITORY':publish_mcpb_release.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_SHA':'a'*40}),patch.object(publish_mcpb_release,'api') as request:
            with self.assertRaisesRegex(ValueError,'selected workflow revision'):publish_mcpb_release.main(self.root)
            request.assert_not_called()

    def test_release_rejects_changed_tag_and_asset(self):
        receipt=package_mcpb.build(self.root)
        env={'GITHUB_REPOSITORY':publish_mcpb_release.REPO,'GITHUB_REF':'refs/heads/main','GITHUB_SHA':receipt['source_commit']}
        with patch.dict(os.environ,env),patch.object(publish_mcpb_release,'api',side_effect=[None,{'object':{'type':'commit','sha':'b'*40}}]):
            with self.assertRaisesRegex(ValueError,'no overwrite'):publish_mcpb_release.main(self.root)
        (self.root/receipt['filename']).write_bytes(b'changed')
        with patch.dict(os.environ,env),patch.object(publish_mcpb_release,'api') as request:
            with self.assertRaisesRegex(ValueError,'changed after build'):publish_mcpb_release.main(self.root)
            request.assert_not_called()

    def test_registry_readback_rejects_wrong_package(self):
        package_mcpb.build(self.root)
        server=json.loads((self.root/'server.json').read_text());server['packages'][0]['fileSha256']='0'*64
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self):return json.dumps({'server':server}).encode()
        with patch.object(check_registry,'urlopen',return_value=Response()):
            with self.assertRaisesRegex(ValueError,'packages differs'):check_registry.check(self.root/'server.json')


if __name__=='__main__':unittest.main()
