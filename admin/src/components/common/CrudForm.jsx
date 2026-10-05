import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useLanguage } from '../../contexts/LanguageContext.jsx'

/**
 * Chuỗi rỗng từ input number → undefined để field `required: false` thực sự là tuỳ chọn
 * (z.coerce.number() sẽ biến '' thành 0, không phân biệt được "bỏ trống" và 0 thật).
 */
function emptyStringToUndefined(value) {
  if (value === '' || value === null || value === undefined) return undefined
  return Number(value)
}

/**
 * Chuỗi rỗng/null → undefined cho field optional kiểu chuỗi (email).
 * KHÔNG được dùng `emptyStringToUndefined` ở đây: Number("user@gmail.com") = NaN
 * làm zod báo "Expected string, received nan" dù người dùng nhập đúng.
 */
function emptyStringToBlankUndefined(value) {
  if (value === '' || value === null || value === undefined) return undefined
  return value
}

// Cùng rule với BE (_ProvisionUserRequest.validate_password_strength): chữ hoa, chữ thường và chữ số.
const PASSWORD_STRENGTH = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/

function createSchema(fields) {
  const shape = {}
  fields.forEach((field) => {
    if (field.type === 'number') {
      const typeMessage = `${field.label} phải là số`
      let rule = z.coerce.number({ invalid_type_error: typeMessage })
      if (field.required === false) {
        let optionalRule = z.number({ invalid_type_error: typeMessage })
        if (field.min !== undefined) optionalRule = optionalRule.min(field.min, `${field.label} phải từ ${field.min}`)
        if (field.max !== undefined) optionalRule = optionalRule.max(field.max, `${field.label} không được lớn hơn ${field.max}`)
        shape[field.name] = z.preprocess(emptyStringToUndefined, optionalRule.optional())
        return
      }
      if (field.min !== undefined) rule = rule.min(field.min, `${field.label} phải từ ${field.min}`)
      if (field.max !== undefined) rule = rule.max(field.max, `${field.label} không được lớn hơn ${field.max}`)
      shape[field.name] = rule
      return
    }

    // Email tuỳ chọn: bỏ trống thì bỏ qua kiểm tra định dạng (giữ hành vi cũ cho email bắt buộc).
    let rule = z.string()
    if (field.required !== false) rule = rule.trim().min(1, `Vui lòng nhập ${field.label.toLowerCase()}`)
    else if (field.type === 'email') {
      shape[field.name] = z.preprocess(emptyStringToBlankUndefined, z.string().email('Email chưa đúng định dạng').optional())
      return
    }
    if (field.minLength) rule = rule.min(field.minLength, `${field.label} cần ít nhất ${field.minLength} ký tự`)
    if (field.type === 'email') rule = rule.email('Email chưa đúng định dạng')
    if (field.type === 'password' && field.required !== false) {
      rule = rule.regex(PASSWORD_STRENGTH, `${field.label} cần có chữ hoa, chữ thường và chữ số`)
    }
    shape[field.name] = rule
  })
  return z.object(shape)
}

export default function CrudForm({ fields, defaultValues = {}, onSubmit, onCancel, submitLabel = 'Lưu thay đổi', loading = false }) {
  const { t } = useLanguage()
  // Các page thường khai báo `fields`/`defaultValues` inline ngay trong render → identity đổi mỗi lần
  // render. Nếu memo theo identity thì `initialValues` luôn mới → useEffect reset chạy vô hạn
  // ("Maximum update depth exceeded"). Dùng JSON làm key: chỉ đổi khi nội dung thật sự đổi.
  const fieldsKey = JSON.stringify(fields)
  const defaultKey = JSON.stringify(defaultValues)
  const schema = useMemo(() => createSchema(JSON.parse(fieldsKey)), [fieldsKey])
  const initialValues = useMemo(() => {
    const defs = JSON.parse(defaultKey)
    return Object.fromEntries(
      JSON.parse(fieldsKey).map((field) => [field.name, defs[field.name] ?? field.defaultValue ?? '']),
    )
  }, [fieldsKey, defaultKey])
  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: initialValues,
  })

  useEffect(() => reset(initialValues), [initialValues, reset])

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
      <div className="grid gap-5 sm:grid-cols-2">
        {fields.map((field) => (
          <label key={field.name} className={field.fullWidth ? 'sm:col-span-2' : ''}>
            <span className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">
              {t(field.label)} {field.required !== false && <span className="text-rose-500">*</span>}
            </span>
            {field.type === 'textarea' ? (
              <textarea rows={field.rows || 4} className="input-control resize-y" placeholder={field.placeholder ? t(field.placeholder) : undefined} disabled={field.disabled} {...register(field.name)} />
            ) : field.type === 'select' ? (
              <select className="input-control" disabled={field.disabled} {...register(field.name)}>
                <option value="">{t('common.select_placeholder', { field: t(field.label) })}</option>
                {field.options?.map((option) => (
                  <option key={option.value} value={option.value}>{t(option.label)}</option>
                ))}
              </select>
            ) : (
              <input
                type={field.type || 'text'}
                min={field.min}
                step={field.step}
                className="input-control"
                placeholder={field.placeholder ? t(field.placeholder) : undefined}
                disabled={field.disabled}
                {...register(field.name)}
              />
            )}
            {field.hint && !errors[field.name] && <span className="mt-1.5 block text-xs text-slate-400 dark:text-slate-500">{t(field.hint)}</span>}
            {errors[field.name] && <span className="mt-1.5 block text-xs font-medium text-rose-600 dark:text-rose-400">{t(errors[field.name].message)}</span>}
          </label>
        ))}
      </div>
      <div className="flex justify-end gap-3 border-t border-slate-100 pt-5 dark:border-slate-800">
        {onCancel && <button type="button" className="btn-secondary" onClick={onCancel}>{t('common.cancel')}</button>}
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? t('common.saving') : t(submitLabel)}</button>
      </div>
    </form>
  )
}
