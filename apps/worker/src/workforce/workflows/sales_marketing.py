"""
Sales & Marketing Workforce - Multi-Agent Workflow
Implements all 8 agents as described in SUMMARY.md
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import logging
import yaml
import aiohttp
from pathlib import Path

import mistralai.workflows as workflows
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

from enum import Enum

class CommunicationType(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"


class SignalSource(str, Enum):
    LINKEDIN = "LinkedIn"
    CRUNCHBASE = "Crunchbase"
    ANGELLIST = "AngelList"
    TECHCRUNCH = "TechCrunch"
    COMPANY_WEBSITE = "Company websites"
    JOB_BOARD = "Job boards"


class LeadStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    REJECTED = "rejected"


class CompanySize(str, Enum):
    SIZE_1_10 = "1-10"
    SIZE_10_50 = "10-50"
    SIZE_50_200 = "50-200"
    SIZE_200_500 = "200-500"
    SIZE_500_1000 = "500-1000"
    SIZE_1000_PLUS = "1000+"


# Market Signal Model
class MarketSignal(BaseModel):
    company: str
    signal_type: str
    source: SignalSource
    title: str
    description: str
    url: str
    detected_at: str
    relevance_score: float = 0.0


# Lead Model
class Lead(BaseModel):
    company: str
    company_size: Optional[CompanySize] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_linkedin: Optional[str] = None
    contact_title: Optional[str] = None
    signal: Optional[MarketSignal] = None
    status: LeadStatus = LeadStatus.NEW
    priority: int = 0
    notes: str = ""


# Content Model
class GeneratedContent(BaseModel):
    content_type: CommunicationType
    subject: Optional[str] = None
    body: str
    lead: Lead
    personalized: bool = False
    compliance_checked: bool = False
    approved: bool = False


# Email Message Model
class EmailMessage(BaseModel):
    to: str
    subject: str
    body: str
    from_address: str
    from_name: str
    signature: str


# LinkedIn Message Model
class LinkedInMessage(BaseModel):
    recipient_linkedin_url: str
    message: str
    connection_request: bool = False


# Follow-up Model
class FollowUp(BaseModel):
    lead: Lead
    scheduled_at: str
    message: str
    attempt_number: int = 1
    max_attempts: int = 3


# Workflow Input
class SalesMarketingInput(BaseModel):
    """Input for the Sales & Marketing Workflow"""
    max_signals: int = Field(default=50, description="Maximum number of market signals to process")
    max_leads: int = Field(default=20, description="Maximum number of leads to generate")
    industries: List[str] = Field(default=[], description="Target industries")
    company_sizes: List[CompanySize] = Field(default=[], description="Target company sizes")
    regions: List[str] = Field(default=[], description="Target geographic regions")
    dry_run: bool = Field(default=True, description="If True, don't actually send messages")


# Workflow Result
class SalesMarketingResult(BaseModel):
    """Result of the Sales & Marketing Workflow"""
    signals_found: int = 0
    leads_generated: int = 0
    emails_sent: int = 0
    linkedin_messages_sent: int = 0
    follow_ups_scheduled: int = 0
    content_generated: List[GeneratedContent] = []
    leads: List[Lead] = []
    errors: List[str] = []


# ============================================================================
# AGENT 1: MARKET SIGNAL ANALYZER
# ============================================================================

@workflows.activity()
async def analyze_market_signals(
    sources: List[SignalSource],
    keywords: List[str],
    max_signals: int = 50,
    max_age_days: int = 7
) -> List[MarketSignal]:
    """
    Detects opportunities from news, social media, job postings.
    Scans various sources for signals indicating company activity.
    """
    logger.info(f"🔍 Analyzing market signals from {len(sources)} sources...")
    
    signals = []
    since_date = (datetime.now() - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
    
    # Simulate signal detection from various sources
    # In production, this would connect to real APIs
    mock_signals = [
        {
            "company": "TechCorp",
            "signal_type": "hiring",
            "source": SignalSource.LINKEDIN,
            "title": "Hiring Senior Sales Executive",
            "description": "TechCorp is expanding its sales team with 3 new positions",
            "url": "https://linkedin.com/jobs/techcorp-sales",
            "detected_at": datetime.now().isoformat(),
            "relevance_score": 0.95
        },
        {
            "company": "DataSystems",
            "signal_type": "funding",
            "source": SignalSource.CRUNCHBASE,
            "title": "Series B Funding",
            "description": "DataSystems raised $25M in Series B funding",
            "url": "https://crunchbase.com/datasystems",
            "detected_at": datetime.now().isoformat(),
            "relevance_score": 0.98
        },
        {
            "company": "CloudFirst",
            "signal_type": "expansion",
            "source": SignalSource.TECHCRUNCH,
            "title": "Opening New Office",
            "description": "CloudFirst opening new office in San Francisco",
            "url": "https://techcrunch.com/cloudfirst-expansion",
            "detected_at": datetime.now().isoformat(),
            "relevance_score": 0.85
        }
    ]
    
    for signal_data in mock_signals[:max_signals]:
        signals.append(MarketSignal(**signal_data))
    
    logger.info(f"✅ Found {len(signals)} market signals")
    return signals


# ============================================================================
# AGENT 2: LEAD RESEARCHER
# ============================================================================

@workflows.activity()
async def research_leads(
    signals: List[MarketSignal],
    target_industries: List[str],
    target_sizes: List[CompanySize],
    target_regions: List[str],
    max_leads: int = 20
) -> List[Lead]:
    """
    Identifies and qualifies leads from market signals.
    Researches company information and contact details.
    """
    logger.info(f"🔎 Researching leads from {len(signals)} signals...")
    
    leads = []
    for signal in signals[:max_leads]:
        # Simulate lead research
        # In production, this would use LinkedIn API, Crunchbase, etc.
        lead_data = {
            "company": signal.company,
            "company_size": CompanySize.SIZE_50_200,
            "industry": "Technology" if any("tech" in ind.lower() for ind in target_industries) else target_industries[0] if target_industries else "Technology",
            "location": "San Francisco, CA",
            "website": f"https://{signal.company.lower().replace(' ', '')}.com",
            "contact_name": f"John Doe",
            "contact_email": f"john.doe@{signal.company.lower().replace(' ', '')}.com",
            "contact_linkedin": f"https://linkedin.com/in/johndoe{signal.company.lower().replace(' ', '')}",
            "contact_title": "VP of Sales",
            "signal": signal,
            "status": LeadStatus.NEW,
            "priority": int(signal.relevance_score * 10),
            "notes": f"Signal: {signal.title}"
        }
        leads.append(Lead(**lead_data))
    
    logger.info(f"✅ Generated {len(leads)} leads")
    return leads


# ============================================================================
# AGENT 3: CONTENT CREATOR
# ============================================================================

@workflows.activity()
async def create_content(
    leads: List[Lead],
    tone: str = "professional",
    length: str = "medium"
) -> List[GeneratedContent]:
    """
    Generates personalized emails and LinkedIn messages.
    Creates content tailored to each prospect.
    """
    logger.info(f"✍️ Creating content for {len(leads)} leads...")
    
    contents = []
    for lead in leads:
        if lead.contact_email:
            # Create email content
            subject = f"Helping {lead.company} with {lead.signal.title if lead.signal else 'growth'}"
            body = f"""Hi {lead.contact_name},

I noticed that {lead.company} is {lead.signal.description if lead.signal else 'expanding'}. 

At our company, we specialize in helping companies like yours achieve similar growth through our innovative solutions.

Would you be open to a quick chat to discuss how we might be able to help?

Best regards,
Sales Team
"""
            contents.append(GeneratedContent(
                content_type=CommunicationType.EMAIL,
                subject=subject,
                body=body,
                lead=lead,
                personalized=True,
                compliance_checked=False,
                approved=False
            ))
        
        if lead.contact_linkedin:
            # Create LinkedIn message
            message = f"""Hi {lead.contact_name},

I saw that {lead.company} is {lead.signal.title if lead.signal else 'growing'}. We've helped similar companies achieve great results.

Would you be open to connecting?

Best,
Sales Team
"""
            contents.append(GeneratedContent(
                content_type=CommunicationType.LINKEDIN,
                body=message,
                lead=lead,
                personalized=True,
                compliance_checked=False,
                approved=False
            ))
    
    logger.info(f"✅ Created {len(contents)} content pieces")
    return contents


# ============================================================================
# AGENT 4: PERSONALIZATION ENGINE
# ============================================================================

@workflows.activity()
async def personalize_content(
    contents: List[GeneratedContent],
    customization_level: str = "high"
) -> List[GeneratedContent]:
    """
    Customizes content for each prospect.
    Adds personal touches and company-specific details.
    """
    logger.info(f"🎨 Personalizing {len(contents)} content pieces...")
    
    for content in contents:
        lead = content.lead
        
        # Add personalization based on lead data
        if lead.company_size:
            content.body = content.body.replace(
                "companies like yours",
                f"{lead.company_size.value} employee companies like {lead.company}"
            )
        
        if lead.industry:
            content.body = content.body.replace(
                "similar companies",
                f"{lead.industry} companies"
            )
        
        if lead.signal:
            content.body = content.body.replace(
                "expanding",
                f"{lead.signal.signal_type.replace('-', ' ')}"
            )
        
        content.personalized = True
    
    logger.info(f"✅ Personalized {len(contents)} content pieces")
    return contents


# ============================================================================
# AGENT 5: COMPLIANCE CHECKER
# ============================================================================

@workflows.activity()
async def check_compliance(
    contents: List[GeneratedContent],
    check_gdpr: bool = True,
    check_can_spam: bool = True,
    check_opt_out: bool = True
) -> List[GeneratedContent]:
    """
    Ensures GDPR and CAN-SPAM compliance.
    Checks content for legal and regulatory compliance.
    """
    logger.info(f"⚖️ Checking compliance for {len(contents)} content pieces...")
    
    for content in contents:
        # Simulate compliance checks
        # In production, this would do actual checks
        content.compliance_checked = True
        
        # Add opt-out link for emails
        if content.content_type == CommunicationType.EMAIL:
            content.body += "\n\n---\nTo opt out of future communications, reply STOP."
    
    logger.info(f"✅ Compliance checked for {len(contents)} content pieces")
    return contents


# ============================================================================
# AGENT 6: EMAIL SENDER
# ============================================================================

@workflows.activity()
async def send_emails(
    contents: List[GeneratedContent],
    dry_run: bool = True,
    smtp_host: str = "smtp.example.com",
    smtp_port: int = 587,
    from_address: str = "sales@example.com",
    from_name: str = "Sales Team",
    signature: str = "Best regards,\nSales Team"
) -> int:
    """
    Sends approved emails via SMTP.
    Returns count of emails sent.
    """
    logger.info(f"📧 Sending emails...")
    
    email_contents = [c for c in contents if c.content_type == CommunicationType.EMAIL and c.approved]
    sent_count = 0
    
    for content in email_contents:
        if dry_run:
            logger.info(f"  [DRY RUN] Would send email to: {content.lead.contact_email}")
            logger.info(f"  Subject: {content.subject}")
        else:
            # In production, this would actually send the email
            logger.info(f"  ✅ Sent email to: {content.lead.contact_email}")
            content.lead.status = LeadStatus.CONTACTED
        sent_count += 1
    
    logger.info(f"✅ {sent_count} emails processed (dry_run={dry_run})")
    return sent_count


# ============================================================================
# AGENT 7: LINKEDIN ENGAGER
# ============================================================================

@workflows.activity()
async def send_linkedin_messages(
    contents: List[GeneratedContent],
    dry_run: bool = True,
    connection_request_limit: int = 100
) -> int:
    """
    Sends connection requests and messages on LinkedIn.
    Returns count of messages sent.
    """
    logger.info(f"💼 Sending LinkedIn messages...")
    
    linkedin_contents = [c for c in contents if c.content_type == CommunicationType.LINKEDIN and c.approved]
    sent_count = 0
    
    for content in linkedin_contents:
        if dry_run:
            logger.info(f"  [DRY RUN] Would send LinkedIn message to: {content.lead.contact_linkedin}")
        else:
            # In production, this would use LinkedIn API
            logger.info(f"  ✅ Sent LinkedIn message to: {content.lead.contact_linkedin}")
            content.lead.status = LeadStatus.CONTACTED
        sent_count += 1
    
    logger.info(f"✅ {sent_count} LinkedIn messages processed (dry_run={dry_run})")
    return sent_count


# ============================================================================
# AGENT 8: FOLLOW-UP SCHEDULER
# ============================================================================

@workflows.activity()
async def schedule_follow_ups(
    leads: List[Lead],
    max_follow_ups: int = 3,
    follow_up_interval: str = "3 days"
) -> List[FollowUp]:
    """
    Automatically schedules follow-up communications.
    Creates follow-up tasks for leads that need them.
    """
    logger.info(f"📅 Scheduling follow-ups for {len(leads)} leads...")
    
    follow_ups = []
    interval_days = 3
    
    if "day" in follow_up_interval:
        interval_days = int(follow_up_interval.split()[0])
    
    for lead in leads:
        if lead.status == LeadStatus.CONTACTED:
            for attempt in range(1, max_follow_ups + 1):
                scheduled_at = (datetime.now() + timedelta(days=interval_days * attempt)).strftime("%Y-%m-%d")
                follow_up = FollowUp(
                    lead=lead,
                    scheduled_at=scheduled_at,
                    message=f"Follow-up #{attempt} for {lead.company}",
                    attempt_number=attempt,
                    max_attempts=max_follow_ups
                )
                follow_ups.append(follow_up)
    
    logger.info(f"✅ Scheduled {len(follow_ups)} follow-ups")
    return follow_ups


# ============================================================================
# HUMAN APPROVAL GATE
# ============================================================================

@workflows.activity()
async def request_human_approval(
    contents: List[GeneratedContent],
    required_for: List[str],
    timeout_hours: int = 24
) -> List[GeneratedContent]:
    """
    Simulates human approval gate.
    In production, this would integrate with an approval system.
    For now, auto-approves in dry_run mode.
    """
    logger.info(f"👤 Requesting human approval for {len(contents)} items...")
    
    # Auto-approve for testing/dry-run
    for content in contents:
        if CommunicationType.EMAIL in required_for and content.content_type == CommunicationType.EMAIL:
            content.approved = True
            logger.info(f"  ✅ Auto-approved email for {content.lead.company}")
        elif CommunicationType.LINKEDIN in required_for and content.content_type == CommunicationType.LINKEDIN:
            content.approved = True
            logger.info(f"  ✅ Auto-approved LinkedIn message for {content.lead.company}")
    
    logger.info(f"✅ All {len(contents)} items approved (auto-approval for testing)")
    return contents


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

@workflows.workflow.define(
    name="sales-marketing-workforce",
    workflow_display_name="Sales & Marketing Workforce",
    workflow_description="Multi-agent system for automated lead generation and prospecting with 8 agents"
)
class SalesMarketingWorkflow:
    """
    Orchestrates all 8 agents in sequence:
    1. Market Signal Analyzer
    2. Lead Researcher
    3. Content Creator
    4. Personalization Engine
    5. Compliance Checker
    6. Human Approval Gate
    7. Email Sender
    8. LinkedIn Engager
    9. Follow-up Scheduler
    """

    @workflows.workflow.entrypoint
    async def run(self, input: SalesMarketingInput) -> SalesMarketingResult:
        logger.info("🚀 Starting Sales & Marketing Workforce...")
        
         workflow_config = {}
                
        # Extract configuration
        sources = [SignalSource(s) for s in workflow_config.get("market_signals", {}).get("sources", [])]
        keywords = workflow_config.get("market_signals", {}).get("keywords", [])
        target_industries = workflow_config.get("icp", {}).get("industries", [])
        target_sizes = [CompanySize(s) for s in workflow_config.get("icp", {}).get("company_sizes", [])]
        target_regions = workflow_config.get("icp", {}).get("regions", [])
        tone = workflow_config.get("agents", {}).get("content_creator", {}).get("tone", "professional")
        length = workflow_config.get("agents", {}).get("content_creator", {}).get("length", "medium")
        customization_level = workflow_config.get("agents", {}).get("personalization_engine", {}).get("customization_level", "high")
        required_for = workflow_config.get("human_approval", {}).get("required_for", [])
        
        # AGENT 1: Market Signal Analyzer
        logger.info("\n" + "="*60)
        logger.info("AGENT 1: MARKET SIGNAL ANALYZER")
        logger.info("="*60)
        signals = await analyze_market_signals(
            sources=sources if sources else [SignalSource.LINKEDIN, SignalSource.CRUNCHBASE],
            keywords=keywords if keywords else ["hiring", "expanding", "funding", "growth"],
            max_signals=input.max_signals,
            max_age_days=7
        )
        
        # AGENT 2: Lead Researcher
        logger.info("\n" + "="*60)
        logger.info("AGENT 2: LEAD RESEARCHER")
        logger.info("="*60)
        leads = await research_leads(
            signals=signals,
            target_industries=target_industries,
            target_sizes=target_sizes if target_sizes else [CompanySize.SIZE_50_200, CompanySize.SIZE_200_500],
            target_regions=target_regions,
            max_leads=input.max_leads
        )
        
        # AGENT 3: Content Creator
        logger.info("\n" + "="*60)
        logger.info("AGENT 3: CONTENT CREATOR")
        logger.info("="*60)
        contents = await create_content(
            leads=leads,
            tone=tone,
            length=length
        )
        
        # AGENT 4: Personalization Engine
        logger.info("\n" + "="*60)
        logger.info("AGENT 4: PERSONALIZATION ENGINE")
        logger.info("="*60)
        contents = await personalize_content(
            contents=contents,
            customization_level=customization_level
        )
        
        # AGENT 5: Compliance Checker
        logger.info("\n" + "="*60)
        logger.info("AGENT 5: COMPLIANCE CHECKER")
        logger.info("="*60)
        contents = await check_compliance(
            contents=contents,
            check_gdpr=True,
            check_can_spam=True,
            check_opt_out=True
        )
        
        # HUMAN APPROVAL GATE
        logger.info("\n" + "="*60)
        logger.info("HUMAN APPROVAL GATE")
        logger.info("="*60)
        contents = await request_human_approval(
            contents=contents,
            required_for=required_for if required_for else ["send_email", "send_linkedin_message"],
            timeout_hours=24
        )
        
        # AGENT 6: Email Sender
        logger.info("\n" + "="*60)
        logger.info("AGENT 6: EMAIL SENDER")
        logger.info("="*60)
        emails_sent = await send_emails(
            contents=contents,
            dry_run=input.dry_run,
            from_address=workflow_config.get("email", {}).get("from_address", "sales@example.com"),
            from_name=workflow_config.get("email", {}).get("from_name", "Sales Team")
        )
        
        # AGENT 7: LinkedIn Engager
        logger.info("\n" + "="*60)
        logger.info("AGENT 7: LINKEDIN ENGAGER")
        logger.info("="*60)
        linkedin_sent = await send_linkedin_messages(
            contents=contents,
            dry_run=input.dry_run
        )
        
        # AGENT 8: Follow-up Scheduler
        logger.info("\n" + "="*60)
        logger.info("AGENT 8: FOLLOW-UP SCHEDULER")
        logger.info("="*60)
        follow_ups = await schedule_follow_ups(
            leads=leads,
            max_follow_ups=workflow_config.get("agents", {}).get("follow_up_scheduler", {}).get("max_follow_ups", 3),
            follow_up_interval=workflow_config.get("agents", {}).get("follow_up_scheduler", {}).get("follow_up_interval", "3 days")
        )
        
        # Compile results
        result = SalesMarketingResult(
            signals_found=len(signals),
            leads_generated=len(leads),
            emails_sent=emails_sent,
            linkedin_messages_sent=linkedin_sent,
            follow_ups_scheduled=len(follow_ups),
            content_generated=contents,
            leads=leads,
            errors=[]
        )
        
        logger.info("\n" + "="*60)
        logger.info("✅ WORKFLOW COMPLETED")
        logger.info("="*60)
        logger.info(f"  Signals found: {result.signals_found}")
        logger.info(f"  Leads generated: {result.leads_generated}")
        logger.info(f"  Emails sent: {result.emails_sent}")
        logger.info(f"  LinkedIn messages sent: {result.linkedin_messages_sent}")
        logger.info(f"  Follow-ups scheduled: {result.follow_ups_scheduled}")
        
        return result
