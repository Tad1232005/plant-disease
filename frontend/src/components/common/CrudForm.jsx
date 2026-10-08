import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

function createSchema(fields, language) {
  const shape = {}
  fields.forEach((field) => {
    if (field.type === 'number') {
      let rule = z.coerce.number({ invalid_type_error: language === 'vi' ? `${field.label} phải là số` : `${field.label} must be a number` })
      if (field.min !== undefined) rule = rule.min(field.min, language === 'vi' ? `${field.label} phải từ ${field.min}` : `${field.label} must be at least ${field.min}`)
      shape[field.name] = rule
      return
    }

    let rule = z.string()
    if (field.required === false) {
      if (field.type === 'email') {
        rule = z.string().trim().email(language === 'vi' ? 'Email chưa đúng định dạng' : 'Enter a valid email address').or(z.literal(''))
      } else {
        rule = z.string().optional().or(z.literal(''))
      }
    } else {
      rule = rule.trim().min(1, language === 'vi' ? `Vui lòng nhập ${field.label.toLowerCase()}` : `Enter ${field.label.toLowerCase()}`)
      if (field.minLength) rule = rule.min(field.minLength, language === 'vi' ? `${field.label} cần ít nhất ${field.minLength} ký tự` : `${field.label} must have at least ${field.minLength} characters`)
      if (field.type === 'email') rule = rule.email(language === 'vi' ? 'Email chưa đúng định dạng' : 'Enter a valid email address')
      if (field.pattern) rule = rule.regex(field.pattern.regex, field.pattern.message)
    }
    shape[field.name] = rule
  })
  return z.object(shape)
}

export default function CrudForm({ fields, defaultValues = {}, onSubmit, onCancel, submitLabel, loading = false, error = null }) {
  const { language, t } = usePreferences()
  const resolvedSubmitLabel = submitLabel || t('common.save')
  const schema = useMemo(() => createSchema(fields, language), [fields, language])
  const initialValues = useMemo(
    () => Object.fromEntries(fields.map((field) => [field.name, defaultValues[field.name] ?? field.defaultValue ?? ''])),
    [defaultValues, fields],
  )
  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: initialValues,
  })

  useEffect(() => reset(initialValues), [initialValues, reset])

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
      {error && (
        <div className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-800">
          <AlertCircle size={18} className="mt-0.5 shrink-0 text-rose-600" />
          <div className="flex-1 leading-relaxed">{error}</div>
        </div>
      )}
      <div className="grid gap-5 sm:grid-cols-2">
        {fields.map((field) => (
          <label key={field.name} className={field.fullWidth ? 'sm:col-span-2' : ''}>
            <span className="mb-2 block text-sm font-semibold text-slate-700">
              {field.label} {field.required !== false && <span className="text-rose-500">*</span>}
            </span>
            {field.type === 'textarea' ? (
              <textarea rows={field.rows || 4} className="input-control resize-y" placeholder={field.placeholder} {...register(field.name)} />
            ) : field.type === 'select' ? (
              <select className="input-control" {...register(field.name)}>
                <option value="">-- {t('common.select')} {field.label.toLowerCase()} --</option>
                {field.options?.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            ) : (
              <input
                type={field.type || 'text'}
                min={field.min}
                step={field.step}
                className="input-control"
                placeholder={field.placeholder}
                {...register(field.name)}
              />
            )}
            {field.hint && !errors[field.name] && <span className="mt-1.5 block text-xs text-slate-400">{field.hint}</span>}
            {errors[field.name] && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors[field.name].message}</span>}
          </label>
        ))}
      </div>
      <div className="flex justify-end gap-3 border-t border-slate-100 pt-5">
        {onCancel && <button type="button" className="btn-secondary" onClick={onCancel}>{t('common.cancel')}</button>}
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? t('common.saving') : resolvedSubmitLabel}</button>
      </div>
    </form>
  )
}
