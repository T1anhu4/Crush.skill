import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Crush.skill'))
from engines.weflow.privacy import sanitize_session, sanitize_text, split_quote
from engines.weflow_import import buildMemoryFromImportedChat


@pytest.mark.parametrize('text,secrets', [
    ('我叫测试甲，住在测试路八号，在示例大学上课', ['测试甲', '测试路八号', '示例大学']),
    ('我的名字是测试乙。我在示例科技公司上班，今天好累', ['测试乙', '示例科技公司']),
    ('姓名：测试丙\n学校：示例 大学\n公司：示例 工作室\n今天好开心', ['测试丙', '示例 大学', '示例 工作室']),
    ('My name is Alice Example. I live at 42 Example Road. I work at Example Labs.', ['Alice Example', '42 Example Road', 'Example Labs']),
    ('I study at Example University. Name: Alice Example\nSee you tomorrow!', ['Example University', 'Alice Example']),
    ('电话是13800138000，微信wxid_test，a@example.com https://example.com/a', ['13800138000', 'wxid_test', 'a@example.com', 'https://example.com/a']),
])
def test_safe_redacts_explicit_identifiers(text, secrets):
    result = sanitize_text(text)
    assert all(secret not in result for secret in secrets)
    assert sanitize_text(text, 'full') == ' '.join(text.split())


@pytest.mark.parametrize('text', [
    '我叫你明天过来，今天好开心', '我叫了外卖，等会儿吃',
    '在家里上课也好累，住在心里的人', '公司今天放假了，学校附近有奶茶',
    'I am happy. I work hard. Call me tomorrow.',
    '学校：示例大学，明天见！',
])
def test_conversation_boundaries(text):
    expected = text.replace('示例大学', '[已脱敏]')
    assert sanitize_text(text) == expected


def test_multiline_identity_does_not_consume_next_sentence():
    assert sanitize_text('姓名：测试丙\n今天好开心') == '姓名：[已脱敏] 今天好开心'


def test_label_value_on_next_line_and_english_sentence_boundary():
    assert sanitize_text('姓名：\n测试丙\n今天好开心') == '姓名：[已脱敏] 今天好开心'
    assert sanitize_text('Name: Alice Example. See you tomorrow!') == 'Name:[已脱敏]. See you tomorrow!'


def test_english_ordinary_locations_are_preserved():
    assert sanitize_text('I work at home. I study at home.') == 'I work at home. I study at home.'


def test_quoted_identity_and_speaker():
    reply, quoted, speaker = split_quote('明天见[引用 原始姓名：我叫测试甲，住在测试路八号]', 'me')
    assert reply == '明天见'
    assert speaker == 'target'
    assert all(secret not in str(quoted) for secret in ['测试甲', '测试路八号', '原始姓名'])


@pytest.mark.parametrize('mode', ['FULL', 'raw', '', None, True])
def test_invalid_privacy_mode_fails_closed(mode):
    with pytest.raises(ValueError):
        sanitize_text('我叫测试甲', mode)
    with pytest.raises(ValueError):
        sanitize_session({}, mode)


def test_safe_bundle_drops_metadata_identifiers_and_media_paths():
    source = {'weflow': {}, 'session': {'wxid': 'wxid_secret', 'nickname': 'Raw Person'}, 'messages': [
        {'localId': 1, 'createTime': 1, 'type': '文本消息', 'content': '我叫测试甲，明天见', 'senderDisplayName': 'Raw Person', 'senderUsername': 'raw_user', 'isSend': 0},
        {'localId': 2, 'createTime': 2, 'type': '图片消息', 'content': '/Users/raw_user/private-photo.jpg', 'isSend': 0},
    ]}
    safe = buildMemoryFromImportedChat(source).to_dict()
    serialized = json.dumps(safe, ensure_ascii=False)
    assert all(secret not in serialized for secret in ['Raw Person', 'raw_user', 'private-photo.jpg', 'wxid_secret', '测试甲'])
    assert safe['stats']['privacy_warning']
    full = json.dumps(buildMemoryFromImportedChat(source, 'full').to_dict(), ensure_ascii=False)
    assert all(secret in full for secret in ['Raw Person', 'raw_user', 'private-photo.jpg', 'wxid_secret', '测试甲'])


@pytest.mark.parametrize('payload', [
    {'privacy_mode': 'private'}, {'privacy_mode': None}, {'full': 'false'},
    {'full': 1}, {'privacy_mode': 'safe', 'full': True},
    {'privacy_mode': 'safe', 'privacy': 'full'},
])
def test_runtime_invalid_or_conflicting_privacy_selection_rejected(payload):
    from execute import CrushSkillRuntime
    # Validation must run before memory persistence (no initialized runtime needed).
    source = json.dumps({'weflow': {}, 'session': {}, 'messages': [
        {'localId': 1, 'createTime': 1, 'type': '文本消息', 'content': '你好'},
    ]})
    with pytest.raises(ValueError):
        CrushSkillRuntime.__new__(CrushSkillRuntime).weflow_import_mode('test', {'source_text': source, **payload})
