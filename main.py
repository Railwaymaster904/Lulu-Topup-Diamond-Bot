import logging

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

from config import BOT_TOKEN
import database as db
from states import UserStates, AdminStates
import handlers as h


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# POST INIT
# ============================================================

async def post_init(application: Application):
    await db.init_db()
    logger.info("✅ Database initialized successfully!")


# ============================================================
# MAIN
# ============================================================

def main():

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ========================================================
    # USER CONVERSATIONS
    # ========================================================

    deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.deposit_method,
                pattern=r"^deposit_(bkash|nagad|rocket|binance)$",
            )
        ],
        states={
            UserStates.WAITING_DEPOSIT_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_deposit_amount,
                )
            ],
            UserStates.WAITING_TRX_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_trx_id,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.select_offer,
                pattern=r"^select_offer_",
            )
        ],
        states={
            UserStates.WAITING_UID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.receive_uid,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # ========================================================
    # ADMIN CONVERSATIONS
    # ========================================================

    add_offer_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_offer_start,
                pattern=r"^add_offer$",
            )
        ],
        states={
            AdminStates.ADD_OFFER_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_name,
                )
            ],
            AdminStates.ADD_OFFER_DIAMONDS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_diamonds,
                )
            ],
            AdminStates.ADD_OFFER_PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_price,
                )
            ],
            AdminStates.ADD_OFFER_BUTTON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_button,
                )
            ],
            AdminStates.ADD_OFFER_DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_description,
                )
            ],
            AdminStates.ADD_OFFER_DELIVERY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_offer_delivery,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    ban_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.ban_user_start,
                pattern=r"^ban_user$",
            )
        ],
        states={
            AdminStates.BAN_USER_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.ban_user_id,
                )
            ],
            AdminStates.BAN_REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.ban_reason,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    unban_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.unban_user_start,
                pattern=r"^unban_user$",
            )
        ],
        states={
            AdminStates.UNBAN_USER_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.unban_user_id,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    add_balance_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_balance_start,
                pattern=r"^add_balance$",
            )
        ],
        states={
            AdminStates.ADD_BALANCE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_balance_user,
                )
            ],
            AdminStates.ADD_BALANCE_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_balance_amount,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    remove_balance_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.remove_balance_start,
                pattern=r"^remove_balance$",
            )
        ],
        states={
            AdminStates.REMOVE_BALANCE_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.remove_balance_user,
                )
            ],
            AdminStates.REMOVE_BALANCE_AMOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.remove_balance_amount,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    reject_deposit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.reject_deposit_start,
                pattern=r"^reject_deposit_",
            )
        ],
        states={
            AdminStates.REJECT_DEPOSIT_REASON: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.reject_deposit_reason,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.broadcast_start,
                pattern=r"^admin_broadcast$",
            )
        ],
        states={
            AdminStates.BROADCAST_MESSAGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.broadcast_message,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    add_promo_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_promo_start,
                pattern=r"^admin_promo$",
            )
        ],
        states={
            AdminStates.ADD_PROMO_CODE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_code,
                )
            ],
            AdminStates.ADD_PROMO_DISCOUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_discount,
                )
            ],
            AdminStates.ADD_PROMO_USES: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_uses,
                )
            ],
            AdminStates.ADD_PROMO_MIN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_min,
                )
            ],
            AdminStates.ADD_PROMO_EXPIRY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_promo_expiry,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    search_user_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.search_user_start,
                pattern=r"^search_user$",
            )
        ],
        states={
            AdminStates.SEARCH_USER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.search_user,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    edit_setting_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.edit_setting_start,
                pattern=r"^set_",
            )
        ],
        states={
            AdminStates.EDIT_SETTING_VALUE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.edit_setting_value,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    add_admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.add_admin_start,
                pattern=r"^add_admin$",
            )
        ],
        states={
            AdminStates.ADD_ADMIN_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.add_admin_id,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # --------------------------------------------------------

    remove_admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                h.remove_admin_start,
                pattern=r"^remove_admin$",
            )
        ],
        states={
            AdminStates.REMOVE_ADMIN_ID: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    h.remove_admin_id,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", h.cancel)
        ],
        allow_reentry=True,
    )

    # ========================================================
    # COMMAND HANDLERS
    # ========================================================

    application.add_handler(
        CommandHandler("start", h.start)
    )

    application.add_handler(
        CommandHandler("dashboard", h.dashboard)
    )

    application.add_handler(
        CommandHandler("cancel", h.cancel)
    )

    # ========================================================
    # CONVERSATION HANDLERS
    # ========================================================

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

    # ========================================================
    # USER CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.back_to_main,
            pattern=r"^back_to_main$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.diamond_topup,
            pattern=r"^diamond_topup$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.special_offers,
            pattern=r"^special_offers$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.deposit_start,
            pattern=r"^deposit$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.my_account,
            pattern=r"^my_account$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.my_orders,
            pattern=r"^my_orders$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.referral,
            pattern=r"^referral$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.support,
            pattern=r"^support$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.help_command,
            pattern=r"^help$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.confirm_order,
            pattern=r"^confirm_order_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_order,
            pattern=r"^cancel_order$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.change_language,
            pattern=r"^change_language$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.set_language,
            pattern=r"^lang_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.check_join,
            pattern=r"^check_join$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.buy_weekly,
            pattern=r"^buy_weekly$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.buy_monthly,
            pattern=r"^buy_monthly$",
        )
    )

    # ========================================================
    # ADMIN CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.dashboard,
            pattern=r"^admin_dashboard$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.close_dashboard,
            pattern=r"^close_dashboard$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_offers_menu,
            pattern=r"^admin_offers$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_users_menu,
            pattern=r"^admin_users$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_deposits_menu,
            pattern=r"^admin_deposits$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_orders_menu,
            pattern=r"^admin_orders$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_stats,
            pattern=r"^admin_stats$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_settings,
            pattern=r"^admin_settings$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.admin_management,
            pattern=r"^admin_management$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.download_users,
            pattern=r"^download_users$",
        )
    )

    # ========================================================
    # OFFER ADMIN
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.all_offers_admin,
            pattern=r"^all_offers$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.save_offer,
            pattern=r"^save_offer$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_add_offer,
            pattern=r"^cancel_add_offer$",
        )
    )

    # ========================================================
    # DEPOSIT ADMIN
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.pending_deposits,
            pattern=r"^pending_deposits$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.approve_deposit,
            pattern=r"^approve_deposit_",
        )
    )

    # ========================================================
    # ORDER ADMIN
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.pending_orders,
            pattern=r"^pending_orders$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.process_order,
            pattern=r"^process_order_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.complete_order,
            pattern=r"^complete_order_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_order_admin,
            pattern=r"^cancel_order_admin_",
        )
    )

    # ========================================================
    # USER MANAGEMENT
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.all_users,
            pattern=r"^all_users$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.quick_ban,
            pattern=r"^quick_ban_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.quick_unban,
            pattern=r"^quick_unban_",
        )
    )

    # ========================================================
    # BROADCAST
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.broadcast_all,
            pattern=r"^broadcast_all$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.cancel_broadcast,
            pattern=r"^cancel_broadcast$",
        )
    )

    # ========================================================
    # SETTINGS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            h.toggle_force_join,
            pattern=r"^toggle_force_join$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            h.toggle_maintenance,
            pattern=r"^toggle_maintenance$",
        )
    )

    # ========================================================
    # START BOT
    # ========================================================

    logger.info("🚀 Bot is starting...")

    application.run_polling(
        allowed_updates=["message", "callback_query"]
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
