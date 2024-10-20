from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards import settings_keyboard, to_home
from bot.states import settings
from models import User



router = Router()


@router.callback_query(F.data == 'settings')
async def refresh(callback_query: CallbackQuery, session: AsyncSession, state: FSMContext):
    user = await session.get(User, callback_query.from_user.id)    
    if user.sell_slippage is None or user.buy_slippage is None:
        user.sell_slippage = 5
        user.buy_slippage = 5
        await session.commit()
        await session.refresh(user)


    text = ('Settings:\n\n'

        'SLIPPAGE CONFIG\n'
        'Customize your slippage settings for buys and sells. Tap to edit.\n'
        )
    
    await callback_query.message.edit_caption(
        caption=text,
        reply_markup=settings_keyboard(user)

    )
    await state.update_data(user=user)

    await callback_query.answer()



@router.callback_query(F.data.startswith('slippage_config'))
async def slippage_config(callback_query: CallbackQuery, state: FSMContext):
    option = callback_query.data.split('_')[2]
    data = await state.get_data()
    user = data.get('user')

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
    user = await session.get(User, callback_query.from_user.id)    
    user.extra_confirmation = not user.extra_confirmation
    await session.commit()

    await callback_query.answer()
    await callback_query.message.edit_reply_markup(
        reply_markup=settings_keyboard(user)
    )
