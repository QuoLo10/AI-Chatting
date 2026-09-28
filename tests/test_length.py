"""
Unit Test Suite for Milestone M2: Dynamic Response Length Controller & Persona Prompts.
Tests determine_response_length, LengthTier, LengthDecision, and prompt generation.
Zero external network or API key dependencies.
"""

import json
import pytest
from pydantic import ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.core.length_controller import (
    LengthTier,
    LengthDecision,
    determine_response_length,
)
from src.core.prompts import (
    build_system_prompt,
    get_chat_prompt_template,
)
from src.ingestion.persona_profile import (
    SLANG_DICTIONARY,
    PROHIBITED_TOKENS,
    FEW_SHOT_EXCHANGES,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_short_decision():
    return LengthDecision(
        tier=LengthTier.SHORT,
        max_tokens=35,
        guidance_instruction="Trả lời cực ngắn từ 1-5 từ, cộc lốc, tự nhiên."
    )


@pytest.fixture
def mock_medium_decision():
    return LengthDecision(
        tier=LengthTier.MEDIUM,
        max_tokens=75,
        guidance_instruction="Trả lời vừa phải từ 6-15 từ, tự nhiên, thân thiện."
    )


@pytest.fixture
def mock_long_decision():
    return LengthDecision(
        tier=LengthTier.LONG,
        max_tokens=160,
        guidance_instruction="Trả lời sâu sắc từ 20-50 từ, rõ ràng ranh giới tình cảm."
    )


@pytest.fixture
def sample_casual_history():
    return [
        HumanMessage(content="Chúc An mai thi tốt"),
        AIMessage(content="Cám mơn ql nhieu nhaa\n☺️"),
    ]


@pytest.fixture
def sample_emotional_history():
    return [
        HumanMessage(content="Thật sự muốn đc bên An vì nhiều lí do (((="),
        AIMessage(content="Muốn đồng ý lắm nhưng mà tiếc là không được..."),
    ]


# ==============================================================================
# Suite 1: TestLengthTierEnum
# ==============================================================================

class TestLengthTierEnum:
    def test_enum_members_exist(self):
        assert hasattr(LengthTier, "SHORT")
        assert hasattr(LengthTier, "MEDIUM")
        assert hasattr(LengthTier, "LONG")

    def test_enum_values(self):
        assert LengthTier.SHORT.value == "short"
        assert LengthTier.MEDIUM.value == "medium"
        assert LengthTier.LONG.value == "long"

    def test_enum_str_inheritance(self):
        assert isinstance(LengthTier.SHORT, str)
        assert LengthTier.SHORT == "short"
        assert LengthTier.MEDIUM == "medium"
        assert LengthTier.LONG == "long"

    def test_enum_construction_from_string(self):
        assert LengthTier("short") is LengthTier.SHORT
        assert LengthTier("medium") is LengthTier.MEDIUM
        assert LengthTier("long") is LengthTier.LONG

    def test_enum_invalid_value_raises(self):
        with pytest.raises(ValueError):
            LengthTier("extra_long")


# ==============================================================================
# Suite 2: TestLengthDecisionModel
# ==============================================================================

class TestLengthDecisionModel:
    def test_valid_length_decision_construction(self, mock_short_decision):
        assert mock_short_decision.tier == LengthTier.SHORT
        assert mock_short_decision.max_tokens == 35
        assert "1-5 từ" in mock_short_decision.guidance_instruction

    def test_model_dump_dict(self, mock_short_decision):
        data = mock_short_decision.model_dump()
        assert data["tier"] == "short"
        assert data["max_tokens"] == 35
        assert isinstance(data["guidance_instruction"], str)

    def test_model_dump_json(self, mock_short_decision):
        raw_json = mock_short_decision.model_dump_json()
        parsed = json.loads(raw_json)
        assert parsed["tier"] == "short"
        assert parsed["max_tokens"] == 35

    def test_invalid_tier_raises_validation_error(self):
        with pytest.raises(ValidationError):
            LengthDecision(tier="invalid_tier", max_tokens=35, guidance_instruction="test")

    def test_invalid_max_tokens_type_raises(self):
        with pytest.raises(ValidationError):
            LengthDecision(tier=LengthTier.SHORT, max_tokens="thirty_five", guidance_instruction="test")

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            LengthDecision(tier=LengthTier.SHORT)


# ==============================================================================
# Suite 3: TestDetermineResponseLengthShort
# ==============================================================================

class TestDetermineResponseLengthShort:
    @pytest.mark.parametrize("greeting", ["ê", "alo", "hi", "chào", "2", "ơi", "helo"])
    def test_greeting_inputs(self, greeting):
        decision = determine_response_length(greeting)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("checkin", ["dậy chưa", "chán quá", "đang đâu", "sao thế"])
    def test_checkin_inputs(self, checkin):
        decision = determine_response_length(checkin)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("affirmation", ["ừ", "ok", "oki", "đúng r", "chuẩn", "ò"])
    def test_affirmation_inputs(self, affirmation):
        decision = determine_response_length(affirmation)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("brief_tease", ["Seen nhanh á", "Ko 😏", "Khổ thân", "Shock z"])
    def test_brief_tease_inputs(self, brief_tease):
        decision = determine_response_length(brief_tease)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_word_count_lte_4_defaults_to_short(self):
        decision = determine_response_length("Hôm nay trời đẹp")
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_short_guidance_instruction_content(self):
        decision = determine_response_length("alo")
        assert decision.guidance_instruction is not None
        assert len(decision.guidance_instruction) > 10

    def test_short_token_upper_bound(self):
        decision = determine_response_length("ê")
        assert decision.max_tokens == 35

    def test_short_with_empty_history(self):
        decision = determine_response_length("ê", conversation_history=[])
        assert decision.tier == LengthTier.SHORT


# ==============================================================================
# Suite 4: TestDetermineResponseLengthMedium
# ==============================================================================

class TestDetermineResponseLengthMedium:
    @pytest.mark.parametrize("text", [
        "Đề của cô mai phương có in ra làm dc kh",
        "Xuất file in tài liệu sao á b",
        "Hôm nay thi môn gì thế An ơi",
    ])
    def test_study_coordination_inputs(self, text):
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    @pytest.mark.parametrize("text", [
        "Tối mai có đi cf với nhóm không?",
        "V tí mình qua bên An lấy tiền mặt nha tầm 12h30",
        "Đi nhậu không 4g chiều nay ở quán cũ",
    ])
    def test_hangout_coordination_inputs(self, text):
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    @pytest.mark.parametrize("text", [
        "Thành bảo chuyển cho Thành tiền bữa trước á ql ơi",
        "Hôm trước ăn hết bao nhiêu tiền để mình gửi lại",
    ])
    def test_debt_and_money_banter_inputs(self, text):
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    def test_general_chat_6_to_15_words(self):
        decision = determine_response_length("Cuối tuần này có rảnh không đi xem phim với nhóm bạn")
        assert decision.tier == LengthTier.MEDIUM
        assert decision.max_tokens <= 75

    def test_medium_guidance_instruction_content(self):
        decision = determine_response_length("Tối mai cf kh b")
        assert decision.guidance_instruction is not None
        assert len(decision.guidance_instruction) > 10

    def test_medium_token_upper_bound(self):
        decision = determine_response_length("Tối mai cf kh b")
        assert decision.max_tokens == 75

    def test_medium_with_casual_history(self, sample_casual_history):
        decision = determine_response_length("Mấy giờ tập trung thế", conversation_history=sample_casual_history)
        assert decision.tier == LengthTier.MEDIUM

    def test_medium_boundary_15_words(self):
        fifteen_words = "một hai ba bốn năm sáu bảy tám chín mười mười một mười hai mười ba mười bốn mười lăm"
        decision = determine_response_length(fifteen_words)
        assert decision.tier == LengthTier.MEDIUM


# ==============================================================================
# Suite 5: TestDetermineResponseLengthLong
# ==============================================================================

class TestDetermineResponseLengthLong:
    def test_confession_input_triggers_long(self):
        text = "Thật sự muốn đc bên An vì nhiều lí do ((((= Nhma An yên tâm khong đc cx ksao đâuuu mình làm bạn thân tiếp cx được màaa."
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    @pytest.mark.parametrize("confession_prompt", [
        "Mình thích An lâu rồi",
        "An làm người yêu mình nha",
        "Mình muốn tỏ tình với An",
    ])
    def test_short_confession_keyword_triggers_long(self, confession_prompt):
        decision = determine_response_length(confession_prompt)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_emotional_venting_triggers_long(self):
        text = "Dạo này mình thấy mệt mỏi và bế tắc quá An ơi, chuyện học hành lẫn gia đình không biết chia sẻ cùng ai..."
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_breakup_grief_triggers_long(self):
        text = "Mình với người yêu vừa chia tay rồi, buồn quá không biết phải làm sao bây giờ An à"
        decision = determine_response_length(text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_long_word_count_gt_25_words_triggers_long(self):
        long_narrative = (
            "Hôm nay mình đi làm từ sáng sớm tới tối mịt mới về đến nhà "
            "vừa mệt vừa đói mà lại gặp phải trời mưa to ngập hết cả đường "
            "không biết ngày mai có kịp hoàn thành bài tập nộp cho thầy không nữa"
        )
        decision = determine_response_length(long_narrative)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_long_guidance_instruction_content(self):
        decision = determine_response_length("Thật sự muốn đc bên An")
        assert decision.guidance_instruction is not None
        assert len(decision.guidance_instruction) > 10

    def test_long_token_upper_bound(self):
        decision = determine_response_length("Thật sự muốn đc bên An")
        assert decision.max_tokens == 160

    def test_long_with_emotional_history(self, sample_emotional_history):
        decision = determine_response_length("An có nghĩ lại không?", conversation_history=sample_emotional_history)
        assert decision.tier == LengthTier.LONG


# ==============================================================================
# Suite 6: TestDetermineResponseLengthEdgeCases
# ==============================================================================

class TestDetermineResponseLengthEdgeCases:
    def test_empty_string_input(self):
        decision = determine_response_length("")
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_whitespace_only_input(self):
        decision = determine_response_length("   \n\t  ")
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("punct", ["???", "!?!?", "...", ".", "!!!"])
    def test_punctuation_only_input(self, punct):
        decision = determine_response_length(punct)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("emoticon", ["=)))", ":))", ":(", ":D", "=))))"])
    def test_emoticon_only_input(self, emoticon):
        decision = determine_response_length(emoticon)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    @pytest.mark.parametrize("emoji", ["😴", "🤡", "🤡🤡🤡", "☕️", "❤"])
    def test_emoji_only_input(self, emoji):
        decision = determine_response_length(emoji)
        assert decision.tier == LengthTier.SHORT
        assert decision.max_tokens <= 35

    def test_massive_text_stress_input(self):
        massive_text = "từ ngữ lặp lại " * 500
        decision = determine_response_length(massive_text)
        assert decision.tier == LengthTier.LONG
        assert decision.max_tokens <= 160

    def test_repeated_tokens_input(self):
        decision = determine_response_length("ê ê ê ê ê ê ê")
        assert decision.tier in (LengthTier.SHORT, LengthTier.MEDIUM)

    def test_foreign_language_input(self):
        decision = determine_response_length("Hey bro what are you doing tonight?")
        assert decision.tier == LengthTier.MEDIUM

    def test_none_conversation_history_accepted(self):
        decision = determine_response_length("alo", conversation_history=None)
        assert decision.tier == LengthTier.SHORT

    def test_invalid_user_input_type_raises(self):
        with pytest.raises((TypeError, ValidationError)):
            determine_response_length(None)

    def test_boundary_exact_word_counts(self):
        four_words = "một hai ba bốn"
        six_words = "một hai ba bốn năm sáu"
        assert determine_response_length(four_words).tier == LengthTier.SHORT
        assert determine_response_length(six_words).tier == LengthTier.MEDIUM


# ==============================================================================
# Suite 7: TestSystemPromptGeneration
# ==============================================================================

class TestSystemPromptGeneration:
    def test_build_system_prompt_default_returns_string(self):
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 200

    def test_vietnamese_language_mandate_enforced(self):
        prompt = build_system_prompt()
        assert "Tiếng Việt" in prompt or "tiếng Việt" in prompt or "VIETNAMESE" in prompt
        # Must mandate Vietnamese response and ban English
        assert "tiếng Anh" in prompt or "English" in prompt

    def test_prohibited_tokens_list_included(self):
        prompt = build_system_prompt()
        for token in ["ko", "k", "đc", "nhma", "oke"]:
            assert token in prompt, f"Expected prohibited token {token} to be listed in system prompt rules."

    def test_slang_dictionary_rules_included(self):
        prompt = build_system_prompt()
        for token in ["kh", "dc", "nma", "r", "=)))"]:
            assert token in prompt, f"Expected slang token {token} to be referenced in system prompt rules."

    def test_anti_ai_formatting_rules_included(self):
        prompt = build_system_prompt()
        # Prompt must forbid AI headings or bullet lists
        prompt_lower = prompt.lower()
        assert "bullet" in prompt_lower or "tiêu đề" in prompt_lower or "danh sách" in prompt_lower or "#" in prompt

    def test_dynamic_guidance_instruction_injected(self, mock_short_decision, mock_long_decision):
        p_short = build_system_prompt(length_decision=mock_short_decision)
        p_long = build_system_prompt(length_decision=mock_long_decision)
        assert mock_short_decision.guidance_instruction in p_short
        assert mock_long_decision.guidance_instruction in p_long

    def test_few_shot_exemplars_injected(self):
        prompt = build_system_prompt(few_shot_category="CASUAL_BANTER", num_few_shots=2)
        assert "User:" in prompt or "ql:" in prompt or "Chúc An mai thi tốt" in prompt

    def test_few_shot_zero_or_invalid_category(self):
        p_zero = build_system_prompt(num_few_shots=0)
        p_invalid = build_system_prompt(few_shot_category="NON_EXISTENT_CATEGORY")
        assert isinstance(p_zero, str) and len(p_zero) > 100
        assert isinstance(p_invalid, str) and len(p_invalid) > 100


# ==============================================================================
# Suite 8: TestChatPromptTemplateIntegration
# ==============================================================================

class TestChatPromptTemplateIntegration:
    def test_get_chat_prompt_template_returns_template(self):
        tpl = get_chat_prompt_template()
        assert isinstance(tpl, ChatPromptTemplate)

    def test_template_input_variables(self):
        tpl = get_chat_prompt_template()
        assert "input" in tpl.input_variables

    def test_template_messages_structure(self):
        tpl = get_chat_prompt_template()
        # Should have system message, history placeholder, and human message
        assert len(tpl.messages) >= 2

    def test_template_format_with_valid_inputs(self):
        tpl = get_chat_prompt_template()
        messages = tpl.format_messages(input="alo", history=[])
        assert len(messages) >= 2
        assert messages[-1].content == "alo"
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[-1], HumanMessage)

    def test_template_format_with_history_turns(self, sample_casual_history):
        tpl = get_chat_prompt_template()
        messages = tpl.format_messages(input="tối mai sao?", history=sample_casual_history)
        # System message (1) + history (2) + human (1) = 4
        assert len(messages) == 1 + len(sample_casual_history) + 1
        assert messages[-1].content == "tối mai sao?"

    def test_custom_system_prompt_override(self):
        custom_prompt = "Đây là prompt tuỳ chỉnh của An An"
        tpl = get_chat_prompt_template(system_prompt=custom_prompt)
        messages = tpl.format_messages(input="test", history=[])
        assert messages[0].content == custom_prompt
