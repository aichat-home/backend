from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import settings_keyboard, to_home
from bot.states import settings
from models import Settings



router = Router()


@router.callback_query(F.data == 'settings')
async def refresh(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    db_settings = await session.get(Settings, callback_query.from_user.id)    
    if db_settings.sell_slippage is None or db_settings.buy_slippage is None:
        db_settings.sell_slippage = 5
        db_settings.buy_slippage = 5
        await session.commit()
        await session.refresh(db_settings)


    text = ('Settings:\n\n'

        'SLIPPAGE CONFIG\n'
        'Customize your slippage settings for buys and sells. Tap to edit.\n'
        )
    
    await callback_query.message.edit_caption(
        caption=text,
        reply_markup=settings_keyboard(db_settings)

    )
    await state.update_data(settings=db_settings)

    await callback_query.answer()



@router.callback_query(F.data.startswith('slippage_config'))
async def slippage_config(callback_query: CallbackQuery, state: FSMContext):
    option = callback_query.data.split('_')[2]

    if option == 'buy':
        await state.set_state(settings.SlippageState.buy_slippage)
    elif option == 'sell':
        await state.set_state(settings.SlippageState.sell_slippage)
    else:
        await callback_query.answer()
        return
    text = f'Enter slippage percentage for {option.capitalize()}'
    await callback_query.message.edit_caption(
        caption=text,
        reply_markup=to_home()
    )


@router.callback_query(F.data == 'change_confirmation')
async def change_confirmation(callback_query: CallbackQuery, session: AsyncSession):
    db_settings = await session.get(Settings, callback_query.from_user.id)    
    db_settings.extra_confirmation = not db_settings.extra_confirmation
    await session.commit()

    await callback_query.answer()
    await callback_query.message.edit_reply_markup(
        reply_markup=settings_keyboard(db_settings)
    )
