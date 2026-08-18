import logging
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)

from config import BOT_TOKEN
import database as db
from states import UserStates, AdminStates
import handlers as h

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    await db.init_db()
    logger.info("✅ Database initialized successfully!")


def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # ==================== USER CONVERSATIONS ====================

    deposit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.deposit_method, pattern="^deposit_(bkash|nagad|rocket|binance)$")],
        states={
            UserStates.WAITING_DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_deposit_amount)
            ],
            UserStates.WAITING_TRX_ID: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_trx_id)
            ],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.select_offer, pattern="^select_offer_")],
        states={
            UserStates.WAITING_UID: [
                MessageHandler(filters.TEXT & \~filters.COMMAND, h.receive_uid)
            ],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # ==================== ADMIN CONVERSATIONS ====================

    add_offer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_offer_start, pattern="^add_offer$")],
        states={
            AdminStates.ADD_OFFER_NAME: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_name)],
            AdminStates.ADD_OFFER_DIAMONDS: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_diamonds)],
            AdminStates.ADD_OFFER_PRICE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_price)],
            AdminStates.ADD_OFFER_BUTTON: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_button)],
            AdminStates.ADD_OFFER_DESCRIPTION: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_description)],
            AdminStates.ADD_OFFER_DELIVERY: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_offer_delivery)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    ban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.ban_user_start, pattern="^ban_user$")],
        states={
            AdminStates.BAN_USER_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.ban_user_id)],
            AdminStates.BAN_REASON: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.ban_reason)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    unban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.unban_user_start, pattern="^unban_user$")],
        states={
            AdminStates.UNBAN_USER_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.unban_user_id)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    add_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_balance_start, pattern="^add_balance$")],
        states={
            AdminStates.ADD_BALANCE_USER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_balance_user)],
            AdminStates.ADD_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_balance_amount)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    remove_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.remove_balance_start, pattern="^remove_balance$")],
        states={
            AdminStates.REMOVE_BALANCE_USER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.remove_balance_user)],
            AdminStates.REMOVE_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.remove_balance_amount)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    reject_deposit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.reject_deposit_start, pattern="^reject_deposit_")],
        states={
            AdminStates.REJECT_DEPOSIT_REASON: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.reject_deposit_reason)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.broadcast_start, pattern="^admin_broadcast$")],
        states={
            AdminStates.BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    add_promo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_promo_start, pattern="^admin_promo$")],
        states={
            AdminStates.ADD_PROMO_CODE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_code)],
            AdminStates.ADD_PROMO_DISCOUNT: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_discount)],
            AdminStates.ADD_PROMO_USES: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_uses)],
            AdminStates.ADD_PROMO_MIN: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_min)],
            AdminStates.ADD_PROMO_EXPIRY: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_promo_expiry)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    search_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.search_user_start, pattern="^search_user$")],
        states={
            AdminStates.SEARCH_USER: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.search_user)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    edit_setting_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.edit_setting_start, pattern="^set_")],
        states={
            AdminStates.EDIT_SETTING_VALUE: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.edit_setting_value)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    add_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.add_admin_start, pattern="^add_admin$")],
        states={
            AdminStates.ADD_ADMIN_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.add_admin_id)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    remove_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(h.remove_admin_start, pattern="^remove_admin$")],
        states={
            AdminStates.REMOVE_ADMIN_ID: [MessageHandler(filters.TEXT & \~filters.COMMAND, h.remove_admin_id)],
        },
        fallbacks=[CommandHandler("cancel", h.cancel)],
        allow_reentry=True
    )

    # ==================== REGISTER HANDLERS ====================

    application.add_handler(CommandHandler("start", h.start))
    application.add_handler(CommandHandler("dashboard", h.dashboard))
    application.add_handler(CommandHandler("cancel", h.cancel))

    application.add_handler(deposit_conv)
    application.add_handler(order_conv)
    application.add_handler(add_offer_conv)
    application.add_handler(ban_conv)
    application.add_handler(unban_conv)
    application.add_handler(add_balance_conv)
    application.add_handler(remove_balance_conv)
    application.add_handler(reject_deposit_conv)
    application.add_handler(broadcast_conv)
    application.add_handler(add_promo_conv)
    application.add_handler(search_user_conv)
    application.add_handler(edit_setting_conv)
    application.add_handler(add_admin_conv)
    application.add_handler(remove_admin_conv)

    # User Callbacks
    application.add_handler(CallbackQueryHandler(h.back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(h.diamond_topup, pattern="^diamond_topup$"))
    application.add_handler(CallbackQueryHandler(h.special_offers, pattern="^special_offers$"))
    application.add_handler(CallbackQueryHandler(h.deposit_start, pattern="^deposit$"))
    application.add_handler(CallbackQueryHandler(h.my_account, pattern="^my_account$"))
    application.add_handler(CallbackQueryHandler(h.my_orders, pattern="^my_orders$"))
    application.add_handler(CallbackQueryHandler(h.referral, pattern="^referral$"))
    application.add_handler(CallbackQueryHandler(h.support, pattern="^support$"))
    application.add_handler(CallbackQueryHandler(h.help_command, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(h.confirm_order, pattern="^confirm_order_"))
    application.add_handler(CallbackQueryHandler(h.cancel_order, pattern="^cancel_order$"))
    application.add_handler(CallbackQueryHandler(h.change_language, pattern="^change_language$"))
    application.add_handler(CallbackQueryHandler(h.set_language, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(h.check_join, pattern="^check_join$"))
    application.add_handler(CallbackQueryHandler(h.buy_weekly, pattern="^buy_weekly$"))
    application.add_handler(CallbackQueryHandler(h.buy_monthly, pattern="^buy_monthly$"))

    # Admin Callbacks
    application.add_handler(CallbackQueryHandler(h.dashboard, pattern="^admin_dashboard$"))
    application.add_handler(CallbackQueryHandler(h.close_dashboard, pattern="^close_dashboard$"))
    application.add_handler(CallbackQueryHandler(h.admin_offers_menu, pattern="^admin_offers$"))
    application.add_handler(CallbackQueryHandler(h.admin_users_menu, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(h.admin_deposits_menu, pattern="^admin_deposits$"))
    application.add_handler(CallbackQueryHandler(h.admin_orders_menu, pattern="^admin_orders$"))
    application.add_handler(CallbackQueryHandler(h.admin_stats, pattern="^admin_stats$"))
    application.add_handler(CallbackQueryHandler(h.admin_settings, pattern="^admin_settings$"))
    application.add_handler(CallbackQueryHandler(h.admin_management, pattern="^admin_management$"))
    application.add_handler(CallbackQueryHandler(h.download_users, pattern="^download_users$"))

    application.add_handler(CallbackQueryHandler(h.all_offers_admin, pattern="^all_offers$"))
    application.add_handler(CallbackQueryHandler(h.save_offer, pattern="^save_offer$"))
    application.add_handler(CallbackQueryHandler(h.cancel_add_offer, pattern="^cancel_add_offer$"))

    application.add_handler(CallbackQueryHandler(h.pending_deposits, pattern="^pending_deposits$"))
    application.add_handler(CallbackQueryHandler(h.approve_deposit, pattern="^approve_deposit_"))

    application.add_handler(CallbackQueryHandler(h.pending_orders, pattern="^pending_orders$"))
    application.add_handler(CallbackQueryHandler(h.process_order, pattern="^process_order_"))
    application.add_handler(CallbackQueryHandler(h.complete_order, pattern="^complete_order_"))
    application.add_handler(CallbackQueryHandler(h.cancel_order_admin, pattern="^cancel_order_admin_"))

    application.add_handler(CallbackQueryHandler(h.all_users, pattern="^all_users$"))
    application.add_handler(CallbackQueryHandler(h.quick_ban, pattern="^quick_ban_"))
    application.add_handler(CallbackQueryHandler(h.quick_unban, pattern="^quick_unban_"))

    application.add_handler(CallbackQueryHandler(h.broadcast_all, pattern="^broadcast_all$"))
    application.add_handler(CallbackQueryHandler(h.cancel_broadcast, pattern="^cancel_broadcast$"))

    application.add_handler(CallbackQueryHandler(h.toggle_force_join, pattern="^toggle_force_join$"))
    application.add_handler(CallbackQueryHandler(h.toggle_maintenance, pattern="^toggle_maintenance$"))

    logger.info("🚀 Bot is starting...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
