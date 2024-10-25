START_TEXT = ('Welcome to BeamBot Trading Bot \n\n'
              

    'Solana Wallet · <a href="https://solscan.io/account/{wallet_address}">🅴</a> (Tap to copy)\n'
    '<code>{wallet_address}</code>\n\n'

    '💳 Balance: 💎 <code>{balance} SOL</code>\n\n'

    'Join BeamBot Community:\n'
    '➤ <a href="https://t.me/BeambotXYZ">Telegram</a> | 𝕏  <a href="https://x.com/BeamBotXYZ">X.com</a>')


CONFIRMATION_TEXT = ('Are you sure you want to export your <b>Private Key?</b>\n\n'

        '<b>🚨WARNING: Never share your private key! 🚨</b>\n'
        'If anyone, including BeamBot team or mods, is asking for your private key, <b>IT IS A SCAM!</b>. Sending it to them will give them <b>full control over your wallet.</b>\n\n'

        'BeamBot team and mods will <b>NEVER</b> ask for your private key.\n\n'
        )


HELP_TEXT = ('Help:\n\n'

    'Which tokens can I trade?\n'
    'Any SPL token that is a SOL pair, on Raydium, pump.fun, Meteora, Moonshot, or Jupiter, and will integrate more platforms on a rolling basis. We pick up pairs instantly.\n\n'

    'Is BeamBot free? How much do I pay for transactions?\n'
    'BeamBot is completely free! We charge {fee}% on transactions, and keep the bot free so that anyone can use it. \n\n'

    'Why is my Net Profit lower than expected?\n'
    'Your Net Profit is calculated after deducting all associated costs, including Price Impact, Transfer Tax, Dex Fees, and a {fee}% BeamBot fee. This ensures the figure you see is what you actually receive, accounting for all transaction-related expenses.\n\n'

    'Further questions? Join our Telegram group: https://t.me/BeambotXYZ\n'
    )


SUCCESSFULL_TRANSACTION = (
    'Transaction Successful! 🎉\n\n'

    '{input_symbol} ({in_amount}) ⟶ {output_symbol} ({out_amount})\n'
    'Fee: {fee_amount}\n'
    'See on <a href="https://solscan.io/tx/{txn_sig}">Solscan</a>\n\n'

    'You get {trading_points} Trading points\n\n'

    'Thank you for choosing our service! 😊'
    )


REFERRALS_TEXT = (
    'Referrals:\n\n'

    'Your reflink: https://t.me/BeamTapBot/Dapp?startapp={referral_code}\n\n'

    'Referrals: {referral_count}\n\n'

    'Sol earned: {sol_earned} SOL\n\n'

    'Rewards are automatically deposited to your wallet.\n\n'

    'Refer your friends and earn 30% of their fees in the first month, 20% in the second and 10% forever!'
)