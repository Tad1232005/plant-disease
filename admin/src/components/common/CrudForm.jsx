import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

function createSchema(fields) {
  const shape = {}
  fields.forEach((field) => {
    if (field.type === 'number') {
      let rule = z.coerce.number({ invalid_type_error: `${field.label} phải là số` })
      if (field.min !== undefined) rule = rule.min(field.min, `${field.label} phải từ ${field.min}`)
      shape[field.name] = rule
      return
    }

    let rule = z.string()
    if (field.required !== false) rule = rule.trim().min(1, `Vui lòng nhập ${field.label.toLowerCase()}`)
    if (field.minLength) rule = rule.min(field.minLength, `${field.label} cần ít nhất ${field.minLength} ký tự`)
    if (field.type === 'email') rule = rule.email('Email chưa đúng định dạng')
    shape[field.name] = rule
  })
  return z.object(shape)
}

export default function CrudForm({ fields, defaultValues = {}, onSubmit, onCancel, submitLabel = 'Lưu thay đổi', loading = false }) {
  const schema = useMemo(() => createSchema(fields), [fields])
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
                <option value="">-- Chọn {field.label.toLowerCase()} --</option>
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
        {onCancel && <button type="button" className="btn-secondary" onClick={onCancel}>Hủy</button>}
        <button type="submit" className="btn-primary" disabled={loading}>{loading ? 'Đang lưu...' : submitLabel}</button>
      </div>
    </form>
  )
}
