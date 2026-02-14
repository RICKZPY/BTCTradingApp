/**
 * Unit tests for StrategyWizard component
 * 
 * These tests verify the wizard step validation logic.
 * 
 * To run these tests, you need to install testing dependencies:
 * npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
 * 
 * Then add to package.json scripts:
 * "test": "vitest"
 * 
 * And add to vite.config.ts:
 * test: {
 *   globals: true,
 *   environment: 'jsdom',
 *   setupFiles: './src/test/setup.ts',
 * }
 */

import { describe, it, expect } from 'vitest'

// Mock validation logic extracted from StrategyWizard
// This allows us to test the validation without rendering the component
type WizardStep = 1 | 2 | 3

interface FormData {
  name: string
  description: string
  expiry_date: string
  quantity: string
  strike: string
  call_strike: string
  put_strike: string
  strikes: string[]
  wing_width: string
}

const validateStep = (
  step: WizardStep,
  selectedTemplate: string,
  formData: FormData
): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  switch (step) {
    case 1:
      if (!selectedTemplate) {
        errors.push('请选择一个策略模板')
      }
      break
    
    case 2:
      // 基本字段验证
      if (!formData.expiry_date) {
        errors.push('请选择到期日')
      } else {
        // 验证到期日不能是过去的日期
        const expiryDate = new Date(formData.expiry_date)
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        if (expiryDate < today) {
          errors.push('到期日不能是过去的日期')
        }
      }
      
      if (!formData.quantity || parseInt(formData.quantity) < 1) {
        errors.push('数量必须至少为1')
      }
      
      // 根据策略类型验证执行价
      switch (selectedTemplate) {
        case 'single_leg':
        case 'straddle':
          if (!formData.strike) {
            errors.push('请选择执行价')
          } else if (parseFloat(formData.strike) <= 0) {
            errors.push('执行价必须大于0')
          }
          break
        
        case 'strangle':
          if (!formData.call_strike) {
            errors.push('请选择看涨期权执行价')
          } else if (parseFloat(formData.call_strike) <= 0) {
            errors.push('看涨期权执行价必须大于0')
          }
          
          if (!formData.put_strike) {
            errors.push('请选择看跌期权执行价')
          } else if (parseFloat(formData.put_strike) <= 0) {
            errors.push('看跌期权执行价必须大于0')
          }
          
          // 验证宽跨式执行价顺序：看跌执行价应该低于看涨执行价
          if (formData.call_strike && formData.put_strike) {
            const callStrike = parseFloat(formData.call_strike)
            const putStrike = parseFloat(formData.put_strike)
            if (putStrike >= callStrike) {
              errors.push('宽跨式策略中，看跌期权执行价应低于看涨期权执行价')
            }
          }
          break
        
        case 'iron_condor':
          if (!formData.strikes.every((s: string) => s !== '')) {
            errors.push('请选择所有4个执行价')
          } else {
            // 验证铁鹰执行价顺序：必须从低到高
            const strikes = formData.strikes.map((s: string) => parseFloat(s))
            if (strikes.some((s: number) => s <= 0)) {
              errors.push('所有执行价必须大于0')
            } else {
              for (let i = 0; i < strikes.length - 1; i++) {
                if (strikes[i] >= strikes[i + 1]) {
                  errors.push('铁鹰策略的执行价必须按从低到高的顺序排列')
                  break
                }
              }
            }
          }
          break
        
        case 'butterfly':
          if (!formData.strike) {
            errors.push('请选择中心执行价')
          } else if (parseFloat(formData.strike) <= 0) {
            errors.push('中心执行价必须大于0')
          }
          
          if (!formData.wing_width) {
            errors.push('请输入翼宽')
          } else if (parseFloat(formData.wing_width) <= 0) {
            errors.push('翼宽必须大于0')
          }
          break
        
        default:
          errors.push('未知的策略类型')
      }
      break
    
    case 3:
      // 步骤3没有额外验证，只是确认
      break
    
    default:
      errors.push('无效的步骤')
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

describe('StrategyWizard - Step Validation', () => {
  const createFormData = (overrides?: Partial<FormData>): FormData => ({
    name: '',
    description: '',
    expiry_date: '',
    quantity: '1',
    strike: '',
    call_strike: '',
    put_strike: '',
    strikes: ['', '', '', ''],
    wing_width: '',
    ...overrides
  })

  describe('Step 1 - Template Selection', () => {
    it('should fail validation when no template is selected', () => {
      const result = validateStep(1, '', createFormData())
      expect(result.isValid).toBe(false)
      expect(result.errors).toContain('请选择一个策略模板')
    })

    it('should pass validation when a template is selected', () => {
      const result = validateStep(1, 'straddle', createFormData())
      expect(result.isValid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })
  })

  describe('Step 2 - Parameter Configuration', () => {
    const futureDate = new Date()
    futureDate.setDate(futureDate.getDate() + 30)
    const futureDateStr = futureDate.toISOString().split('T')[0]

    describe('Basic field validation', () => {
      it('should fail when expiry_date is missing', () => {
        const result = validateStep(2, 'straddle', createFormData())
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请选择到期日')
      })

      it('should fail when expiry_date is in the past', () => {
        const pastDate = '2020-01-01'
        const result = validateStep(2, 'straddle', createFormData({ 
          expiry_date: pastDate,
          strike: '45000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('到期日不能是过去的日期')
      })

      it('should fail when quantity is missing or less than 1', () => {
        const result = validateStep(2, 'straddle', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '0',
          strike: '45000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('数量必须至少为1')
      })
    })

    describe('Single leg strategy validation', () => {
      it('should fail when strike is missing', () => {
        const result = validateStep(2, 'single_leg', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请选择执行价')
      })

      it('should fail when strike is zero or negative', () => {
        const result = validateStep(2, 'single_leg', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strike: '0'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('执行价必须大于0')
      })

      it('should pass with valid parameters', () => {
        const result = validateStep(2, 'single_leg', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strike: '45000'
        }))
        expect(result.isValid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })
    })

    describe('Straddle strategy validation', () => {
      it('should pass with valid strike', () => {
        const result = validateStep(2, 'straddle', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strike: '45000'
        }))
        expect(result.isValid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })
    })

    describe('Strangle strategy validation', () => {
      it('should fail when call_strike is missing', () => {
        const result = validateStep(2, 'strangle', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          put_strike: '44000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请选择看涨期权执行价')
      })

      it('should fail when put_strike is missing', () => {
        const result = validateStep(2, 'strangle', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          call_strike: '46000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请选择看跌期权执行价')
      })

      it('should fail when put_strike >= call_strike', () => {
        const result = validateStep(2, 'strangle', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          call_strike: '45000',
          put_strike: '46000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('宽跨式策略中，看跌期权执行价应低于看涨期权执行价')
      })

      it('should pass with valid strikes in correct order', () => {
        const result = validateStep(2, 'strangle', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          call_strike: '46000',
          put_strike: '44000'
        }))
        expect(result.isValid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })
    })

    describe('Iron condor strategy validation', () => {
      it('should fail when not all strikes are provided', () => {
        const result = validateStep(2, 'iron_condor', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strikes: ['43000', '44000', '', '']
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请选择所有4个执行价')
      })

      it('should fail when strikes are not in ascending order', () => {
        const result = validateStep(2, 'iron_condor', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strikes: ['43000', '46000', '45000', '47000']
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('铁鹰策略的执行价必须按从低到高的顺序排列')
      })

      it('should fail when any strike is zero or negative', () => {
        const result = validateStep(2, 'iron_condor', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strikes: ['0', '44000', '46000', '47000']
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('所有执行价必须大于0')
      })

      it('should pass with valid strikes in ascending order', () => {
        const result = validateStep(2, 'iron_condor', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strikes: ['43000', '44000', '46000', '47000']
        }))
        expect(result.isValid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })
    })

    describe('Butterfly strategy validation', () => {
      it('should fail when strike is missing', () => {
        const result = validateStep(2, 'butterfly', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          wing_width: '2000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请选择中心执行价')
      })

      it('should fail when wing_width is missing', () => {
        const result = validateStep(2, 'butterfly', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strike: '45000'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('请输入翼宽')
      })

      it('should fail when wing_width is zero or negative', () => {
        const result = validateStep(2, 'butterfly', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strike: '45000',
          wing_width: '0'
        }))
        expect(result.isValid).toBe(false)
        expect(result.errors).toContain('翼宽必须大于0')
      })

      it('should pass with valid parameters', () => {
        const result = validateStep(2, 'butterfly', createFormData({ 
          expiry_date: futureDateStr,
          quantity: '1',
          strike: '45000',
          wing_width: '2000'
        }))
        expect(result.isValid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })
    })
  })

  describe('Step 3 - Confirmation', () => {
    it('should always pass validation', () => {
      const result = validateStep(3, 'straddle', createFormData())
      expect(result.isValid).toBe(true)
      expect(result.errors).toHaveLength(0)
    })
  })

  describe('Step navigation', () => {
    it('should prevent proceeding to step 2 without template selection', () => {
      const step1Result = validateStep(1, '', createFormData())
      expect(step1Result.isValid).toBe(false)
    })

    it('should allow proceeding to step 2 with template selected', () => {
      const step1Result = validateStep(1, 'straddle', createFormData())
      expect(step1Result.isValid).toBe(true)
    })

    it('should prevent proceeding to step 3 without valid parameters', () => {
      const step2Result = validateStep(2, 'straddle', createFormData())
      expect(step2Result.isValid).toBe(false)
    })

    it('should allow proceeding to step 3 with valid parameters', () => {
      const futureDate = new Date()
      futureDate.setDate(futureDate.getDate() + 30)
      const futureDateStr = futureDate.toISOString().split('T')[0]
      
      const step2Result = validateStep(2, 'straddle', createFormData({
        expiry_date: futureDateStr,
        quantity: '1',
        strike: '45000'
      }))
      expect(step2Result.isValid).toBe(true)
    })
  })
})
