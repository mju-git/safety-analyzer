import React, { useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [ingredientsText, setIngredientsText] = useState('')
  const [productName, setProductName] = useState('')
  const [category, setCategory] = useState('')
  const [activeTab, setActiveTab] = useState('search') // 'search' or 'ingredients'
  const [products, setProducts] = useState([])
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Helper to detect if input is a barcode (all digits, 8-14 characters)
  const isBarcode = (input) => {
    const cleaned = input.trim().replace(/\s/g, '')
    return /^\d{8,14}$/.test(cleaned)
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query or barcode')
      return
    }

    setLoading(true)
    setError(null)
    setProducts([])
    setSelectedProduct(null)
    setAnalysis(null)

    const query = searchQuery.trim()
    
    // Detect if input is a barcode (all digits, 8-14 characters)
    if (isBarcode(query)) {
      // Handle as barcode
      try {
        const response = await fetch(
          `${API_BASE_URL}/scan/barcode`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              barcode: query
            })
          }
        )
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }))
          throw new Error(errorData.detail || `Barcode scan failed: ${response.statusText}`)
        }

        const product = await response.json()
        setProducts([product])  // Barcode returns single product
        setSelectedProduct(product)
        
        // Automatically analyze the product
        if (product.id) {
          // Small delay to ensure state is set
          setTimeout(() => {
            handleProductSelect(product)
          }, 100)
        }
      } catch (err) {
        setError(err.message || 'Failed to scan barcode')
      } finally {
        setLoading(false)
      }
    } else {
      // Handle as text search
      try {
        const response = await fetch(
          `${API_BASE_URL}/search/products?q=${encodeURIComponent(query)}`
        )
        
        if (!response.ok) {
          throw new Error(`Search failed: ${response.statusText}`)
        }

        const data = await response.json()
        setProducts(data)
        
        if (data.length === 0) {
          setError('No products found in local database. 💡 Tip: Use barcode search (enter 8-14 digits) to find products from Open Food Facts. Text search only works for products already in the database.')
        }
      } catch (err) {
        setError(err.message || 'Failed to search products')
      } finally {
        setLoading(false)
      }
    }
  }

  const handleAnalyzeIngredients = async () => {
    if (!ingredientsText.trim()) {
      setError('Please enter ingredient list')
      return
    }

    setLoading(true)
    setError(null)
    setProducts([])
    setSelectedProduct(null)
    setAnalysis(null)

    try {
      const requestBody = {
        ingredients: ingredientsText.trim()
      }
      
      if (productName.trim()) {
        requestBody.product_name = productName.trim()
      }
      
      if (category) {
        requestBody.category = category
      }

      const response = await fetch(
        `${API_BASE_URL}/analyze/by-ingredients`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Validate response structure
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format from server')
      }
      
      if (!data.explanation) {
        data.explanation = {
          flagged_ingredients: [],
          beneficial_ingredients: [],
          recommendation: data.recommendation || 'Analysis completed',
          explanations: []
        }
      }
      
      if (!data.safety_score && data.safety_score !== 0) {
        data.safety_score = 50
      }
      
      // Create a virtual product object for display
      const virtualProduct = {
        id: null,
        name: productName.trim() || 'Custom Product',
        brand: null,
        category: category || 'general'
      }
      
      setSelectedProduct(virtualProduct)
      setAnalysis(data)
    } catch (err) {
      console.error('Error analyzing ingredients:', err)
      setError(err.message || 'Failed to analyze ingredients')
      setAnalysis(null)
    } finally {
      setLoading(false)
    }
  }

  const handleProductSelect = async (product) => {
    setSelectedProduct(product)
    setAnalysis(null)
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/analyze/product`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          product_id: product.id,
          user_profile: {
            sensitive_skin: false,
            pregnant: false,
            child: false
          }
        })
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Analysis API error:', response.status, errorText)
        throw new Error(`Analysis failed: ${response.status} ${response.statusText}`)
      }

      let data
      try {
        data = await response.json()
        console.log('Analysis response:', data)
      } catch (jsonError) {
        console.error('Failed to parse JSON response:', jsonError)
        const text = await response.text()
        console.error('Response text:', text)
        throw new Error(`Invalid JSON response from server: ${text.substring(0, 200)}`)
      }
      
      // Validate response structure
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format from server')
      }
      
      if (!data.explanation) {
        // Ensure explanation exists with default structure
        data.explanation = {
          flagged_ingredients: [],
          beneficial_ingredients: [],
          recommendation: data.recommendation || 'Analysis completed',
          explanations: []
        }
      }
      
      // Ensure all required fields exist
      if (!data.safety_score && data.safety_score !== 0) {
        data.safety_score = 50 // Default neutral score
      }
      
      setAnalysis(data)
    } catch (err) {
      console.error('Error analyzing product:', err)
      setError(err.message || 'Failed to analyze product')
      setAnalysis(null) // Clear analysis on error
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'score-high'
    if (score >= 60) return 'score-medium'
    return 'score-low'
  }

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Low Risk'
    if (score >= 60) return 'Moderate Risk'
    return 'High Risk'
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Product Safety Analyzer</h1>
        <p>Search for products and analyze their safety</p>
      </div>

      {/* Tab Selector */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', borderBottom: '2px solid #ecf0f1' }}>
        <button
          onClick={() => {
            setActiveTab('search')
            setError(null)
            setProducts([])
            setSelectedProduct(null)
            setAnalysis(null)
          }}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: activeTab === 'search' ? '#3498db' : 'transparent',
            color: activeTab === 'search' ? 'white' : '#7f8c8d',
            cursor: 'pointer',
            fontWeight: activeTab === 'search' ? 'bold' : 'normal',
            borderBottom: activeTab === 'search' ? '3px solid #2980b9' : '3px solid transparent',
            marginBottom: '-2px'
          }}
        >
          Search Products
        </button>
        <button
          onClick={() => {
            setActiveTab('ingredients')
            setError(null)
            setProducts([])
            setSelectedProduct(null)
            setAnalysis(null)
          }}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: activeTab === 'ingredients' ? '#3498db' : 'transparent',
            color: activeTab === 'ingredients' ? 'white' : '#7f8c8d',
            cursor: 'pointer',
            fontWeight: activeTab === 'ingredients' ? 'bold' : 'normal',
            borderBottom: activeTab === 'ingredients' ? '3px solid #2980b9' : '3px solid transparent',
            marginBottom: '-2px'
          }}
        >
          Analyze by Ingredients
        </button>
      </div>

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="search-section">
          <input
            type="text"
            className="search-input"
            placeholder="Search by name or scan barcode (e.g., 'nutella' or '3017620422003')"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            className="search-button"
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? (isBarcode(searchQuery) ? 'Scanning...' : 'Searching...') : 'Search'}
          </button>
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#7f8c8d' }}>
            💡 Tip: Enter 8-14 digits to search by barcode (finds products from Open Food Facts). Text search only finds products already in the database.
          </div>
        </div>
      )}

      {/* Ingredients Analysis Tab */}
      {activeTab === 'ingredients' && (
        <div className="search-section">
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              Product Name (optional)
            </label>
            <input
              type="text"
              className="search-input"
              placeholder="e.g., 'Fanta Orange'"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
            />
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              Category (optional)
            </label>
            <select
              className="search-input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ padding: '0.75rem' }}
            >
              <option value="">Select category...</option>
              <option value="food">Food</option>
              <option value="cosmetic">Cosmetic</option>
              <option value="household">Household</option>
              <option value="supplement">Supplement</option>
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              Ingredient List *
            </label>
            <textarea
              className="search-input"
              placeholder="Paste ingredient list here (comma-separated or one per line)&#10;Example: Water, Sugar, Carbon Dioxide, Citric Acid, Natural Flavors"
              value={ingredientsText}
              onChange={(e) => setIngredientsText(e.target.value)}
              rows={6}
              style={{ 
                resize: 'vertical',
                fontFamily: 'inherit',
                fontSize: '0.95rem'
              }}
            />
          </div>
          
          <button
            className="search-button"
            onClick={handleAnalyzeIngredients}
            disabled={loading}
            style={{ backgroundColor: '#27ae60' }}
          >
            {loading ? 'Analyzing...' : 'Analyze Ingredients'}
          </button>
          
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#7f8c8d' }}>
            💡 Paste the ingredient list from any product label. The system will analyze each ingredient and provide a safety assessment.
          </div>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {products.length > 0 && (
        <div className="product-list">
          <h2 className="section-title">Search Results</h2>
          {products.map((product) => (
            <div
              key={product.id}
              className={`product-item ${
                selectedProduct?.id === product.id ? 'selected' : ''
              }`}
              onClick={() => handleProductSelect(product)}
            >
              <div className="product-name">{product.name}</div>
              {product.brand && (
                <div className="product-brand">Brand: {product.brand}</div>
              )}
              <div className="product-category">
                {product.category}
              </div>
            </div>
          ))}
        </div>
      )}

      {loading && selectedProduct && (
        <div className="loading">Analyzing product...</div>
      )}

      {!loading && selectedProduct && !analysis && !error && (
        <div className="loading">Click on a product to analyze it</div>
      )}

      {analysis && selectedProduct && (
        <div className="analysis-section">
          {/* Product Header */}
          <div className="product-header">
            <h2 className="product-title">{selectedProduct.name || 'Unknown Product'}</h2>
            {selectedProduct.brand && (
              <div className="product-brand-header">by {selectedProduct.brand}</div>
            )}
            <div className="product-category-badge">{selectedProduct.category || 'N/A'}</div>
          </div>

          {/* Safety Score - Prominent Display */}
          <div className="safety-score">
            <div className="score-container">
              <div className={`score-value ${getScoreColor(analysis.safety_score || 50)}`}>
                {analysis.safety_score !== undefined ? analysis.safety_score : 50}
              </div>
              <div className="score-label">{getScoreLabel(analysis.safety_score || 50)}</div>
            </div>
          </div>

          {/* Product Summary */}
          {analysis.explanation && analysis.explanation.product_summary && (
            <div className="product-summary">
              <div className="product-summary-header">
                <h3 className="section-title">Product Safety Summary</h3>
                <div className="verdict-badge-container">
                  <span className={`verdict-badge verdict-${analysis.explanation.product_summary.verdict.toLowerCase().replace(/\s+/g, '-')}`}>
                    {analysis.explanation.product_summary.verdict}
                  </span>
                  {analysis.explanation.product_summary.confidence && (
                    <span className={`confidence-badge confidence-${analysis.explanation.product_summary.confidence.toLowerCase()}`}>
                      {analysis.explanation.product_summary.confidence} Confidence
                    </span>
                  )}
                </div>
              </div>
              
              {analysis.explanation.product_summary.summary && (
                <div className="summary-text">
                  {analysis.explanation.product_summary.summary}
                </div>
              )}

              {analysis.explanation.product_summary.key_factors && 
               analysis.explanation.product_summary.key_factors.length > 0 && (
                <div className="key-factors">
                  <h4 className="key-factors-title">Key Contributing Factors:</h4>
                  <ul className="key-factors-list">
                    {analysis.explanation.product_summary.key_factors.map((factor, idx) => (
                      <li key={idx} className="key-factor-item">{factor}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Recommendation */}
          {analysis.explanation && analysis.explanation.recommendation && (
            <div className="recommendation">
              <strong>Recommendation:</strong> {analysis.explanation.recommendation}
            </div>
          )}
          
          {analysis.explanation && !analysis.explanation.recommendation && (
            <div className="recommendation">
              <strong>Note:</strong> Analysis completed. No specific recommendation available.
            </div>
          )}

          {/* Ingredient Summary */}
          {analysis.explanation && analysis.explanation.ingredient_summary && (
            <div className="ingredient-summary">
              <h3 className="section-title">Ingredients Analyzed: {analysis.explanation.ingredient_summary.total || 0}</h3>
              {analysis.explanation.overall_confidence && (
                <div className="confidence-indicator">
                  Overall Confidence: <span className={`confidence-${analysis.explanation.overall_confidence}`}>
                    {analysis.explanation.overall_confidence}
                  </span>
                </div>
              )}
              {/* Unresolved Ingredient Information */}
              {analysis.explanation.unresolved_ingredient_count !== undefined && 
               analysis.explanation.unresolved_ingredient_count > 0 && (
                <div style={{ 
                  marginTop: '1rem', 
                  padding: '1rem', 
                  backgroundColor: '#f8f9fa', 
                  borderLeft: '4px solid #6c757d',
                  borderRadius: '4px'
                }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: '#495057' }}>
                    ℹ️ Data Coverage: {analysis.explanation.unresolved_ingredient_count} of {analysis.explanation.total_ingredient_count} ingredients unresolved
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#6c757d', lineHeight: '1.6' }}>
                    {analysis.explanation.unresolved_ingredient_explanation}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Class 1: Known & Assessed (Moderate/High Risk) */}
          {analysis.explanation && analysis.explanation.flagged_ingredients &&
            analysis.explanation.flagged_ingredients.length > 0 && (
              <div className="flagged-ingredients">
                <h3 className="section-title">⚠️ Moderate/High Concern</h3>
                <div className="ingredients-list">
                  {analysis.explanation.flagged_ingredients.map((ingredient, index) => (
                    <div key={index} className="ingredient-item">
                      <div className="ingredient-header">
                        <div className="ingredient-name">{ingredient.name}</div>
                        <div className="ingredient-badges">
                          {ingredient.risk_level && (
                            <span className={`risk-badge risk-${ingredient.risk_level}`}>
                              {ingredient.risk_level === 'unknown' ? 'unknown' : `${ingredient.risk_level} risk`}
                            </span>
                          )}
                          {ingredient.confidence && (
                            <span className={`confidence-badge confidence-${ingredient.confidence}`}>
                              {ingredient.confidence} confidence
                            </span>
                          )}
                          {ingredient.evidence_source && (
                            <div className="ingredient-source">{ingredient.evidence_source}</div>
                          )}
                        </div>
                      </div>
                      <div className="ingredient-reason">{ingredient.reason}</div>
                      {ingredient.notes && (
                        <div className="ingredient-notes">
                          {typeof ingredient.notes === 'string' 
                            ? ingredient.notes 
                            : Array.isArray(ingredient.notes)
                            ? ingredient.notes.join(', ')
                            : JSON.stringify(ingredient.notes)}
                        </div>
                      )}
                      <div className="ingredient-details">
                        {ingredient.safe_dosage && (
                          <div className="detail-row">
                            <span className="detail-label">Safe dosage:</span>
                            <span className="detail-value">
                              {ingredient.safe_dosage} {ingredient.unit || ''}
                            </span>
                          </div>
                        )}
                        {ingredient.exposure_context && (
                          <div className="detail-row">
                            <span className="detail-label">Exposure:</span>
                            <span className="detail-value">{ingredient.exposure_context}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Class 3: Unknown/Insufficient Data */}
          {analysis.explanation && analysis.explanation.unknown_ingredients &&
            analysis.explanation.unknown_ingredients.length > 0 && (
              <div className="unknown-ingredients-section">
                <h3 className="section-title">ℹ️ Insufficient Data</h3>
                <div className="ingredients-list">
                  {analysis.explanation.unknown_ingredients.map((ingredient, index) => (
                    <div key={index} className="ingredient-item unknown-ingredient">
                      <div className="ingredient-header">
                        <div className="ingredient-name">{ingredient.name}</div>
                        <div className="ingredient-badges">
                          <span className="confidence-badge confidence-low">
                            Low confidence
                          </span>
                        </div>
                      </div>
                      <div className="ingredient-reason">{ingredient.reason}</div>
                      {ingredient.notes && (
                        <div className="ingredient-notes">
                          {typeof ingredient.notes === 'string' 
                            ? ingredient.notes 
                            : Array.isArray(ingredient.notes)
                            ? ingredient.notes.join(', ')
                            : JSON.stringify(ingredient.notes)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Class 2: Known but Low Concern */}
          {analysis.explanation && analysis.explanation.low_concern_ingredients &&
            analysis.explanation.low_concern_ingredients.length > 0 && (
              <div className="low-concern-ingredients">
                <h3 className="section-title">✅ Low Concern</h3>
                <div className="low-concern-list">
                  {analysis.explanation.low_concern_ingredients.map((ingredient, index) => (
                    <div key={index} className="low-concern-item">
                      <div className="low-concern-name">{ingredient.name}</div>
                      {ingredient.notes && (
                        <div className="low-concern-notes">{ingredient.notes}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Beneficial Ingredients (Backward Compatibility) */}
          {analysis.explanation && analysis.explanation.beneficial_ingredients &&
            analysis.explanation.beneficial_ingredients.length > 0 && (
              <div className="beneficial-ingredients">
                <h3 className="section-title">Beneficial Ingredients</h3>
                <div className="beneficial-list">
                  {analysis.explanation.beneficial_ingredients.map((ingredient, index) => {
                    // Handle both object and string formats
                    const name = typeof ingredient === 'string' ? ingredient : ingredient.name || 'Unknown'
                    const benefit = typeof ingredient === 'string' 
                      ? `Contains ${ingredient}, which may provide health benefits`
                      : ingredient.benefit || `Contains ${name}, which may provide health benefits`
                    
                    return (
                      <div key={index} className="beneficial-item">
                        <div className="beneficial-name">{name}</div>
                        <div className="beneficial-benefit">{benefit}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

          {/* All Ingredients - Complete Assessment */}
          {analysis.explanation && analysis.explanation.all_ingredients &&
            analysis.explanation.all_ingredients.length > 0 && (
              <div className="all-ingredients">
                <h3 className="section-title">Complete Ingredient Assessment</h3>
                <p className="section-subtitle">All ingredients found in this product with their safety assessments:</p>
                <div className="ingredients-list">
                  {analysis.explanation.all_ingredients.map((ingredient, index) => {
                    const isUnknown = ingredient.is_unknown || ingredient.risk_level === 'unknown' || ingredient.confidence === 'unknown'
                    const itemClass = isUnknown ? 'ingredient-item unknown-ingredient' : 'ingredient-item'
                    
                    return (
                      <div key={index} className={itemClass}>
                        <div className="ingredient-header">
                          <div className="ingredient-name">{ingredient.name}</div>
                          <div className="ingredient-badges">
                            {ingredient.risk_level && (
                              <span className={`risk-badge risk-${ingredient.risk_level}`}>
                                {ingredient.risk_level === 'unknown' ? 'unknown' : `${ingredient.risk_level} risk`}
                              </span>
                            )}
                            {ingredient.confidence && (
                              <span className={`confidence-badge confidence-${ingredient.confidence}`}>
                                {ingredient.confidence} confidence
                              </span>
                            )}
                            {ingredient.evidence_source && (
                              <div className="ingredient-source">{ingredient.evidence_source}</div>
                            )}
                          </div>
                        </div>
                        {ingredient.reason && (
                          <div className="ingredient-reason">{ingredient.reason}</div>
                        )}
                        {ingredient.notes && (
                          <div className="ingredient-notes">
                            {typeof ingredient.notes === 'string' 
                              ? ingredient.notes 
                              : Array.isArray(ingredient.notes)
                              ? ingredient.notes.join(', ')
                              : JSON.stringify(ingredient.notes)}
                          </div>
                        )}
                        {ingredient.safe_dosage && (
                          <div className="ingredient-details">
                            <div className="detail-row">
                              <span className="detail-label">Safe dosage:</span>
                              <span className="detail-value">
                                {ingredient.safe_dosage} {ingredient.unit || ''}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

          {/* Disclaimer */}
          <div className="disclaimer">
            <h4 className="disclaimer-title">Important Disclaimer</h4>
            <p className="disclaimer-text">
              This analysis is for informational purposes only and is not medical advice. 
              Safety scores are based on available ingredient data and may not account for 
              individual sensitivities, allergies, or specific health conditions. Dosage 
              information reflects general guidelines and may vary by product formulation. 
              Some ingredients may not have complete safety data available. Always consult 
              with healthcare professionals for personalized advice, especially if you have 
              sensitive skin, are pregnant, or have underlying health conditions.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
