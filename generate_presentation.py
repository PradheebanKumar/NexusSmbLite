"""
Generate the complete Course Presentation PPTX for Nexus-SMB Lite.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette matching the course deck: Deep Dark Navy (#0B1120), Purple Accent (#6366F1), White, Light Gray
    COLOR_BG_DARK = RGBColor(11, 17, 32)
    COLOR_CARD_DARK = RGBColor(20, 29, 47)
    COLOR_BG_LIGHT = RGBColor(248, 250, 252)
    COLOR_CARD_LIGHT = RGBColor(255, 255, 255)
    COLOR_PRIMARY = RGBColor(79, 70, 229)     # Indigo / Purple
    COLOR_TEXT_MAIN = RGBColor(15, 23, 42)
    COLOR_TEXT_MUTED = RGBColor(100, 116, 139)
    COLOR_ACCENT_GREEN = RGBColor(16, 185, 129)

    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    def add_header(slide, tag_text, title_text, subtitle_text=""):
        # Category Tag Pill
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(4), Inches(0.4))
        tf_tag = tag_box.text_frame
        tf_tag.word_wrap = True
        p_tag = tf_tag.paragraphs[0]
        p_tag.text = tag_text.upper()
        p_tag.font.size = Pt(10)
        p_tag.font.bold = True
        p_tag.font.color.rgb = COLOR_PRIMARY

        # Main Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.5), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_MAIN

        if subtitle_text:
            p_sub = tf_title.add_paragraph()
            p_sub.text = subtitle_text
            p_sub.font.size = Pt(13)
            p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 1: Title Slide (Dark Theme)
    # ══════════════════════════════════════════════════════════════════════
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1, COLOR_BG_DARK)

    # Top Tag
    tb = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(10), Inches(0.5))
    p = tb.text_frame.paragraphs[0]
    p.text = "4-DAY COURSE · FINAL TEAM PRESENTATION"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = RGBColor(129, 140, 248)

    # Title
    tb_t = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11), Inches(1.6))
    p = tb_t.text_frame.paragraphs[0]
    p.text = "Nexus-SMB Lite"
    p.font.size = Pt(48)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    # Subtitle
    tb_sub = s1.shapes.add_textbox(Inches(1.0), Inches(3.4), Inches(11), Inches(1.2))
    p = tb_sub.text_frame.paragraphs[0]
    p.text = "An Intent-Driven Autonomous AI Workforce and Multimodal Operating System for MSMEs"
    p.font.size = Pt(20)
    p.font.color.rgb = RGBColor(148, 163, 184)

    # Accent Line
    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.0), Inches(4.7), Inches(1.5), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(236, 72, 153)
    line.line.fill.background()

    # Team Info
    tb_team = s1.shapes.add_textbox(Inches(1.0), Inches(5.1), Inches(11), Inches(1.5))
    tf = tb_team.text_frame
    p1 = tf.paragraphs[0]
    p1.text = "Team Members: Pradheeban Kumar & Team"
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)

    p2 = tf.add_paragraph()
    p2.text = "Thiagarajar College of Engineering, Madurai"
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(148, 163, 184)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 2: 1. Start with the Problem
    # ══════════════════════════════════════════════════════════════════════
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2, COLOR_BG_LIGHT)
    add_header(s2, "Problem & Motivation", "1. Start with the Problem", "What is broken today, for whom, and why did your team choose it?")

    cards_data = [
        ("01", "Problem Statement", "Small retail / kirana merchants manage inventory, wholesale bills, and khata manually in paper notebooks. They lack the time for complex software, leading to frequent stockouts, untracked dead stock, and lost customer sales."),
        ("02", "Why This Problem?", "Observed firsthand in local kirana shops: owners spend 2+ hours every evening manually reconciling paper bills. WhatsApp customer inquiries go unanswered while attending counter customers, losing business to quick-commerce apps."),
        ("03", "Target User", "Independent kirana store owners, neighborhood provision shops, and small stationery merchants in Tier-2/3 cities communicating in colloquial languages (Tamil/Tanglish) and WhatsApp.")
    ]

    for idx, (num, title, body) in enumerate(cards_data):
        left = Inches(0.8 + idx * 3.9)
        top = Inches(2.2)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(3.7), Inches(4.4))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_LIGHT
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.word_wrap = True
        p_num = tf.paragraphs[0]
        p_num.text = num
        p_num.font.size = Pt(16)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_PRIMARY

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TEXT_MAIN
        p_t.space_after = Pt(12)

        p_b = tf.add_paragraph()
        p_b.text = body
        p_b.font.size = Pt(13)
        p_b.font.color.rgb = COLOR_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 3: 2. Why Does this Problem Matter? (Impact & Success)
    # ══════════════════════════════════════════════════════════════════════
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3, COLOR_BG_LIGHT)
    add_header(s3, "Impact & Success", "2. Why does this Problem matter?", "Show the Impact before you show the solution.")

    # Left Card: Impact & Evidence
    card_l = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.7))
    card_l.fill.solid()
    card_l.fill.fore_color.rgb = COLOR_CARD_LIGHT
    card_l.line.color.rgb = RGBColor(226, 232, 240)
    tf_l = card_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "Impact / Evidence"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.space_after = Pt(14)

    items_l = [
        "• Time Lost: 10–14 hours weekly spent manually tallying paper distributor invoices and daily register entries.",
        "• Financial Loss: 8–15% of working capital trapped in dead stock (slow-moving items past shelf life).",
        "• Missed Revenue: WhatsApp customer stock queries go unanswered during rush hours, losing buyers to quick-commerce.",
        "• Pricing Errors: Retailers accidentally sell discounted items below cost price without real-time margin visibility."
    ]
    for it in items_l:
        pi = tf_l.add_paragraph()
        pi.text = it
        pi.font.size = Pt(13)
        pi.font.color.rgb = COLOR_TEXT_MUTED
        pi.space_after = Pt(10)

    # Right Card: Success Criteria
    card_r = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(2.0), Inches(5.7), Inches(4.7))
    card_r.fill.solid()
    card_r.fill.fore_color.rgb = COLOR_CARD_LIGHT
    card_r.line.color.rgb = RGBColor(226, 232, 240)
    tf_r = card_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Success Criteria (Observable Outcomes)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.space_after = Pt(14)

    items_r = [
        "• 5-Second Ingestion: Convert handwritten/printed wholesale bills into inventory records instantly using Multimodal Vision.",
        "• Consequential Action Gating: 100% prevention of loss-making price updates via automated human approval holds.",
        "• Sub-10ms Edge Response: 70%+ of customer WhatsApp queries answered instantly via local ML intent classification.",
        "• Zero Hallucination: All stock and pricing answers strictly grounded in live SQLite database records."
    ]
    for it in items_r:
        pi = tf_r.add_paragraph()
        pi.text = it
        pi.font.size = Pt(13)
        pi.font.color.rgb = COLOR_TEXT_MUTED
        pi.space_after = Pt(10)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 4: 3. Show the Intent-Driven Experience
    # ══════════════════════════════════════════════════════════════════════
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4, COLOR_BG_LIGHT)
    add_header(s4, "Product Experience", "3. Show the Intent-Driven Experience", "What changes for the user when your Product orchestrates the work?")

    # Before Card
    cb = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.7))
    cb.fill.solid()
    cb.fill.fore_color.rgb = RGBColor(254, 242, 242)
    cb.line.color.rgb = RGBColor(254, 202, 202)
    tfb = cb.text_frame
    tfb.word_wrap = True
    p = tfb.paragraphs[0]
    p.text = "BEFORE: Manual Fragmented Journey"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = RGBColor(185, 28, 28)
    p.space_after = Pt(14)

    before_steps = [
        "1. Distributor delivers paper bill $\\rightarrow$ Owner manually enters rows into paper register.",
        "2. Customer asks price on WhatsApp $\\rightarrow$ Owner stops counter work to search shelf.",
        "3. Decides to discount slow stock $\\rightarrow$ Manually calculates margin to avoid losses.",
        "4. Customer asks for unavailable product $\\rightarrow$ Signal forgotten; item never restocked.",
        "5. Reconciles sales register at night $\\rightarrow$ 2 hours of repetitive calculation."
    ]
    for s in before_steps:
        pi = tfb.add_paragraph()
        pi.text = s
        pi.font.size = Pt(12)
        pi.font.color.rgb = RGBColor(127, 29, 29)
        pi.space_after = Pt(8)

    # After Card
    ca = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(2.0), Inches(5.7), Inches(4.7))
    ca.fill.solid()
    ca.fill.fore_color.rgb = RGBColor(240, 253, 244)
    ca.line.color.rgb = RGBColor(187, 247, 208)
    tfa = ca.text_frame
    tfa.word_wrap = True
    p = tfa.paragraphs[0]
    p.text = "AFTER: Intent-Driven Agentic Experience"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = RGBColor(21, 128, 61)
    p.space_after = Pt(14)

    after_steps = [
        "1. Express One Goal: Snap paper bill photo $\\rightarrow$ Gemini Vision auto-updates inventory & margins in 5s.",
        "2. Natural Language Actions: 'Sold 20 milk' or 'Bought 10 sugar at 40' $\\rightarrow$ Intent Router executes DB tools directly.",
        "3. Safety Built-In: 'Drop price to 10' $\\rightarrow$ Agent detects selling at a loss $\\rightarrow$ Gates behind PendingAction approval.",
        "4. Autonomous Customer Service: Local hybrid ML bot handles WhatsApp queries with live stock grounding 24/7.",
        "5. Morning Briefing: Proactive orchestrator audits cash flow and dead stock before shop opens."
    ]
    for s in after_steps:
        pi = tfa.add_paragraph()
        pi.text = s
        pi.font.size = Pt(12)
        pi.font.color.rgb = RGBColor(20, 83, 45)
        pi.space_after = Pt(8)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 5: 4. Architecture of the Solution
    # ══════════════════════════════════════════════════════════════════════
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5, COLOR_BG_LIGHT)
    add_header(s5, "Architecture", "4. Architecture of the Solution", "Show the system, not only the chat screen.")

    arch_boxes = [
        ("INPUTS", "Natural Chat & Voice\nMultimodal Bill Photos\nCustomer WhatsApp Queries\nDaily APScheduler Cron"),
        ("SESSION 1: UNDERSTAND", "IntentRouter.decompose()\n• Slot Filling (item, price, qty)\n• Ambiguity Clarification Gate\n• Zero-Hallucination Routing"),
        ("SESSION 3: KNOW & REMEMBER", "ContextGrounder\n• SQLite Source Authority\n• Dynamic Fact Injection\n• 10-turn Rolling Conversation Memory"),
        ("SESSION 2: ACT", "AgentToolRegistry\n• Deterministic Tools\n• Consequential Action Gating (Loss Prevention)\n• Human-in-the-Loop Approvals"),
        ("EVIDENCE & OUTCOME", "Database State Verified\nPendingAction Generated\nWhatsApp Reply Delivered\nDeveloper Trace Rendered in UI")
    ]

    for idx, (title, content) in enumerate(arch_boxes):
        top = Inches(2.0 + idx * 0.95)
        box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.7), Inches(0.82))
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_CARD_LIGHT
        box.line.color.rgb = COLOR_PRIMARY if idx == 1 or idx == 3 else RGBColor(203, 213, 225)

        tf = box.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(12)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_PRIMARY

        p2 = tf.add_paragraph()
        p2.text = content.replace("\n", "   |   ")
        p2.font.size = Pt(11)
        p2.font.color.rgb = COLOR_TEXT_MAIN

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 6: 5. What Did You Use from the Course?
    # ══════════════════════════════════════════════════════════════════════
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6, COLOR_BG_LIGHT)
    add_header(s6, "Course Concepts", "5. What did you use from the Course?", "Do not list buzzwords — Connect each concept to a Design decision.")

    course_data = [
        ("Session 1 · Understand", "Intent · Entities · State · Ambiguity", [
            "• IntentRouter (backend/agents/intent_router.py): Decomposes user goal into QUERY, ACTION, or AMBIGUOUS.",
            "• Slot Extraction: Typed entities (item_name, quantity, price, expense_type).",
            "• Active Ambiguity Resolution: If owner says 'Change price', agent halts and clarifies: 'Which item and what is the new price?' instead of guessing."
        ]),
        ("Session 2 · Act", "Tools · Verification · Approvals · Native Tool Registry", [
            "• Deterministic Tools (backend/agents/tools.py): Python ORM tools for price update, stock adjustment, sales & expense logging.",
            "• Why Native Registry instead of MCP? Low latency in a self-contained retail app; zero IPC serialization overhead.",
            "• Consequential Verification & HITL: If price drop creates negative margin (new_price < cost), execution halts and creates PendingAction for owner approval."
        ]),
        ("Session 3 · Know & Remember", "Source Authority · Grounding · State Continuity", [
            "• Source Authority Grounding: ContextGrounder queries SQLite for live item numbers (stock, margin, velocity) before LLM generates text.",
            "• State Continuity & Memory: 10-turn persistent conversation memory loaded from SQLite conversations table.",
            "• Hybrid ML Edge: TF-IDF char n-grams (backend/ml/) for sub-10ms Tanglish customer intent classification."
        ])
    ]

    for idx, (head, subhead, bullets) in enumerate(course_data):
        top = Inches(2.0 + idx * 1.6)
        card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top, Inches(11.7), Inches(1.45))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_LIGHT
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{head}  —  {subhead}"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_PRIMARY
        p1.space_after = Pt(4)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(11)
            pb.font.color.rgb = COLOR_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 7: 6. Implementation Details
    # ══════════════════════════════════════════════════════════════════════
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7, COLOR_BG_LIGHT)
    add_header(s7, "Implementation", "6. Implementation Details", "Make the architecture concrete: stack, data flow, key decisions and failure handling.")

    impl_cards = [
        ("Tech Stack", [
            "• Frontend: React 18, Vite, TailwindCSS, Lucide-React",
            "• Backend: FastAPI (Python 3.13), SQLAlchemy ORM, SQLite",
            "• AI Brain: Google Gemini 2.5 Flash (Vision & Reasoning)",
            "• Local ML: Scikit-learn (TF-IDF char n-grams + Logistic Regression)",
            "• Task Scheduling: APScheduler for autonomous morning audits"
        ]),
        ("Key Implementation Flow", [
            "1. User Message received via Chat / WhatsApp API",
            "2. IntentRouter decomposes goal & extracts target entities",
            "3. ContextGrounder queries SQLite for live item record",
            "4. AgentToolRegistry evaluates safety & execution policy",
            "5. Safe action updates DB; Risky action gates to PendingAction",
            "6. Returns conversational reply + Developer Trace object"
        ]),
        ("Reliability & Controls", [
            "• Zero-Downtime Fallback: If Gemini API quota fails, local DB fallback answers customer stock questions.",
            "• Loss Guardrail: Selling price cannot be dropped below wholesale cost without explicit owner approval.",
            "• Permissive Transliteration: Character n-grams handle Tanglish and typos (tamato, iruka, evlo).",
            "• Audit Logging: Every intent, tool execution, and approval is saved to SQLite."
        ])
    ]

    for idx, (title, bullets) in enumerate(impl_cards):
        left = Inches(0.8 + idx * 3.9)
        top = Inches(2.0)
        card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(3.7), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_LIGHT
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_MAIN
        p.space_after = Pt(10)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(11)
            pb.font.color.rgb = COLOR_TEXT_MUTED
            pb.space_after = Pt(6)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 8: 7. Working Demo Scenario
    # ══════════════════════════════════════════════════════════════════════
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8, COLOR_BG_LIGHT)
    add_header(s8, "Live Demo", "7. Working Demo Scenario", "The demo should prove the user outcome — not only that the UI loads.")

    demo_steps = [
        ("01", "Demo Scenario", "Demonstrate end-to-end consequential price safety:\nStore owner instructs the AI via Chat: 'Change price of Lorem Souvenir to ₹1.0' (Wholesale cost is ₹3.25)."),
        ("02", "What We Observe", "• Agent Trace badge expands in Chat UI showing:\n  - Intent: ACTION_UPDATE_PRICE\n  - Grounded Source: SQLite (Cost: ₹3.25, Stock: 202)\n  - Safety Gate: Gated: Negative Margin Risk\n• Agent refuses direct database update and explains why."),
        ("03", "Success Evidence", "• Live SQLite Check: Selling price was NOT corrupted.\n• Approvals Page: PendingAction #63 created with title 'Approval Needed: Sell Lorem Souvenir at a Loss?' awaiting owner decision.")
    ]

    for idx, (num, title, body) in enumerate(demo_steps):
        left = Inches(0.8 + idx * 3.9)
        top = Inches(2.0)
        card = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(3.7), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_LIGHT
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.word_wrap = True
        p_num = tf.paragraphs[0]
        p_num.text = num
        p_num.font.size = Pt(16)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_PRIMARY

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TEXT_MAIN
        p_t.space_after = Pt(10)

        p_b = tf.add_paragraph()
        p_b.text = body
        p_b.font.size = Pt(12)
        p_b.font.color.rgb = COLOR_TEXT_MUTED

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 9: 8. Demo Video or Live Demo
    # ══════════════════════════════════════════════════════════════════════
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9, COLOR_BG_DARK)

    tb = s9.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11), Inches(1.0))
    p = tb.text_frame.paragraphs[0]
    p.text = "Live Demonstration & System Walkthrough"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)

    demo_card = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(2.7), Inches(11.3), Inches(3.8))
    demo_card.fill.solid()
    demo_card.fill.fore_color.rgb = COLOR_CARD_DARK
    demo_card.line.color.rgb = RGBColor(51, 65, 85)

    tf_d = demo_card.text_frame
    tf_d.word_wrap = True
    p = tf_d.paragraphs[0]
    p.text = "Key Flows Demonstrated in Real-Time:"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(129, 140, 248)
    p.space_after = Pt(14)

    flows = [
        "1. Multimodal Bill Ingestion: Upload purchase bill photo $\\rightarrow$ Gemini Vision extracts items into inventory in 5s.",
        "2. Ambiguity & Clarification: Type 'Change price' $\\rightarrow$ Agent asks: 'Which item and what price?'",
        "3. Consequential Safety Gate: Type 'Change price of Milk to ₹10' (cost is ₹22) $\\rightarrow$ PendingAction hold triggered.",
        "4. Customer WhatsApp Bot: Tanglish query ('milk iruka?') $\\rightarrow$ Sub-10ms ML classification + grounded live stock response.",
        "5. Developer Trace: Live inspection of Intent, Slot Filling, Grounding flag, and Tool Verification status."
    ]
    for f in flows:
        pf = tf_d.add_paragraph()
        pf.text = f
        pf.font.size = Pt(13)
        pf.font.color.rgb = RGBColor(226, 232, 240)
        pf.space_after = Pt(8)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 10: 9. What Did You Learn? What Would You Improve?
    # ══════════════════════════════════════════════════════════════════════
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10, COLOR_BG_LIGHT)
    add_header(s10, "Learnings & Limitations", "8. What did you Learn? What would you Improve?", "Show engineering judgment, not only a happy-path demo.")

    learn_cards = [
        ("01", "What Worked Well", [
            "• Hybrid edge architecture: Character n-gram ML for Tanglish greetings + Gemini for reasoning saved 70% API calls.",
            "• Consequential action gates completely eliminated accidental inventory/pricing corruption.",
            "• Live SQLite source authority grounding prevented hallucination of product stock and rates."
        ]),
        ("02", "Limitations", [
            "• Sarcasm and extreme regional idioms can still misclassify customer intent.",
            "• Concurrency: SQLite is fine for single stores, but chain stores require PostgreSQL with connection pooling.",
            "• Network dependency: Gemini cloud calls require internet; rural offline operation requires on-device LLM."
        ]),
        ("03", "Next Iteration (1 More Week)", [
            "• Local Edge LLM: Deploy Meta's Llama 3.2 1B / 3B via Ollama for 100% offline edge inference on shop counter PCs.",
            "• WhatsApp Cloud Webhook: Bi-directional customer order placement and automated UPI payment link generation.",
            "• Supplier Auto-Reorder: Direct SMS/WhatsApp dispatch to distributors when items breach low-stock thresholds."
        ])
    ]

    for idx, (num, title, bullets) in enumerate(learn_cards):
        left = Inches(0.8 + idx * 3.9)
        top = Inches(2.0)
        card = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(3.7), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_LIGHT
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.word_wrap = True
        p_num = tf.paragraphs[0]
        p_num.text = num
        p_num.font.size = Pt(16)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_PRIMARY

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_TEXT_MAIN
        p_t.space_after = Pt(10)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = b
            pb.font.size = Pt(11)
            pb.font.color.rgb = COLOR_TEXT_MUTED
            pb.space_after = Pt(6)

    # ══════════════════════════════════════════════════════════════════════
    # SLIDE 11: 10. References & Artifacts
    # ══════════════════════════════════════════════════════════════════════
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11, COLOR_BG_LIGHT)
    add_header(s11, "References & Q&A", "9. References & Artifacts", "Make it easy for reviewers to inspect your work after the presentation.")

    # Left Box: Project Links
    b_l = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.0), Inches(5.6), Inches(4.7))
    b_l.fill.solid()
    b_l.fill.fore_color.rgb = COLOR_CARD_LIGHT
    b_l.line.color.rgb = RGBColor(226, 232, 240)
    tf_l = b_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "Project Links"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.space_after = Pt(14)

    links = [
        "GitHub Repository:",
        "https://github.com/PradheebanKumar/NexusSmbLite",
        "",
        "Active Course Architecture Branch:",
        "feature/course-agent-architecture",
        "",
        "Working Local Demo Environment:",
        "Backend: http://localhost:8000 (FastAPI Docs)",
        "Frontend: http://localhost:5173 (React UI)"
    ]
    for l in links:
        pi = tf_l.add_paragraph()
        pi.text = l
        pi.font.size = Pt(12)
        pi.font.color.rgb = COLOR_PRIMARY if "http" in l or "feature" in l else COLOR_TEXT_MUTED

    # Right Box: References
    b_r = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(2.0), Inches(5.7), Inches(4.7))
    b_r.fill.solid()
    b_r.fill.fore_color.rgb = COLOR_CARD_LIGHT
    b_r.line.color.rgb = RGBColor(226, 232, 240)
    tf_r = b_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "References & External Sources"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.space_after = Pt(14)

    refs = [
        "• Google Gemini 2.5 Flash: Multi-modal document ingestion & agent reasoning.",
        "• Scikit-learn: Character n-gram TF-IDF Vectorization for noisy transliterated text.",
        "• Designing Agents for Intent-Driven Products Course Framework (Sessions 1–3).",
        "• Meta Llama 3.2 Edge Documentation for on-device quantized retail models.",
        "",
        "Thank you! Ready for Q&A."
    ]
    for r in refs:
        pi = tf_r.add_paragraph()
        pi.text = r
        pi.font.size = Pt(12)
        pi.font.color.rgb = COLOR_TEXT_MUTED if "Thank" not in r else COLOR_PRIMARY
        if "Thank" in r:
            pi.font.bold = True
            pi.font.size = Pt(16)

    output_path = "c:\\Users\\Pradheeban Kumar\\OneDrive\\Desktop\\NexusSMBLite\\Nexus_SMB_Lite_Final_Presentation.pptx"
    prs.save(output_path)
    print(f"[SUCCESS] Presentation saved to: {output_path}")

if __name__ == "__main__":
    create_presentation()
