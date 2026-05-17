# Plan: Centered Loading Animation

## Goal
Implement a centered loading animation that appears when a user navigates between pages or when a page is performing its initial data load.

## Approach
1. **CSS Component:** Create a reusable CSS-based spinner that is centered on the viewport using `position: fixed`.
2. **Implementation:** Inject this CSS/HTML at the top of each page script.
3. **Behavior:** Since Streamlit renders top-to-bottom, the spinner will show immediately and remain until the rest of the page components are rendered.

## Affected Files
- `pages/1_Upload.py`
- `pages/2_Sales_Dashboard.py`
- `pages/3_Dealer_Health.py`
- `pages/4_Product_Performance.py`
- `pages/5_Profitability_Dashboard.py`
- `pages/6_Field_Operations.py`
- `pages/7_Lost_Sales.py`
- `pages/8_Admin.py`
- `pages/9_Profile.py`

## CSS Snippet (Conceptual)
```html
<style>
    .centered-loader {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999;
    }
</style>
```

## Verification
- Navigation between dashboards shows the spinner in the center.
- Spinner disappears once the charts/tables are fully loaded.
