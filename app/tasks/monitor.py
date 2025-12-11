import logging
from app.infrastructure.celery import celery_app
from app.services.bot.memory.session import SessionManager
from app.integrations.huggy.service import HuggyService
from app.core.timeouts import TIMEOUT_POLICES

logger = logging.getLogger(__name__)

@celery_app.task(name="check_inactivity")
def check_inactivity(chat_id: int, expected_state: str, sent_at_timestamp: int):
    session = SessionManager()
    huggy = HuggyService()

    # 1. Validações (Se usuário já falou ou mudou de estado, aborta)
    current_state = session.get_state(chat_id)
    last_interaction = session.get_last_interaction(chat_id)

    if current_state != expected_state:
        logger.info(f"🛑 [Monitor] Chat {chat_id} mudou de estado ({current_state}). Task cancelada.")
        return

    if last_interaction > sent_at_timestamp:
        logger.info(f"🛑 [Monitor] Chat {chat_id} interagiu recentemente. Task cancelada.")
        return
    
    rule = TIMEOUT_POLICES.get(expected_state)
    if not rule: return

    logger.info(f"⏰ [Timeout] Executando ({rule['action']}) para Chat {chat_id}")

    if rule['action'] == "TRANSITION":
        huggy.send_message(chat_id, rule['message_key'])

        session.set_state(chat_id, rule['new_state'])

        new_rule = TIMEOUT_POLICES.get(rule['new_state'])
        if new_rule:
            check_inactivity.apply_async(
                args=[chat_id, rule['new_state'], sent_at_timestamp],
                countdown=new_rule['delay']
            )
    
    elif rule['action'] == "KILL":
        huggy.send_message(chat_id, rule['message_key'])

        if rule.get('tabulation_key'):
            tab_id = huggy.tabulations.get(rule['tabulation_key'])
            if tab_id:
                huggy.finish_attendance(chat_id, tabulation_id=tab_id)
        
        session.clear_session(chat_id)