// Account display name from the address: "wout.altepost" for wout.altepost@gmail.com,
// "wout@alpacaai" for wout@alpacaai.nl. The account label from MAIL_ACCOUNTS_JSON
// ("Personal", "Work", ...) is shown as a tag next to it.
export function accountName(account) {
  const email = account?.email || ''
  if (!email) return account?.label || ''
  const [local, domain = ''] = email.split('@')
  if (/^(gmail|googlemail)\.com$/i.test(domain)) return local
  return `${local}@${domain.replace(/\.[a-z]{2,}$/i, '')}`
}
