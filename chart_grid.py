# -*- coding: utf-8 -*-
"""
Multi-Chart Dashboard with Grid Layout
- Edit existing charts via dropdown
- Universal filters apply to all charts
- Draggable & resizable grid layout (requires streamlit-elements)
- Session-only storage
- Custom labels support (title, xlabel, ylabel)

Requirements:
    pip install streamlit-elements==0.1.*
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
import base64
from io import BytesIO

st.set_page_config(page_title="ChartGrid", page_icon="📊", layout="wide")

plt.style.use('seaborn-v0_8-pastel')
sns.set_palette("pastel")


# ============================================================
# SESSION STATE
# ============================================================
for key, default in [('df', None), ('loaded', False), ('filename', None),
                     ('charts', []), ('chart_counter', 0),
                     ('edit_chart_id', None), ('layout', None)]:
    if key not in st.session_state:
        st.session_state[key] = default

def reset():
    st.session_state.df = None
    st.session_state.loaded = False
    st.session_state.filename = None
    st.session_state.charts = []
    st.session_state.chart_counter = 0
    st.session_state.edit_chart_id = None
    st.session_state.layout = None


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 for dashboard display"""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_b64


def render_chart(cfg, plot_df, palette_map):
    """Render a single chart and return matplotlib figure"""
    x_col = cfg['x']
    y_col = cfg['y']
    selected_cols = cfg.get('selected_cols')
    top_n = cfg['top_n']
    use_others = cfg['use_others']
    sort_by = cfg['sort_by']
    sort_order = cfg['sort_order']
    selected_palette = palette_map[cfg['color']]
    chart_type = cfg['type']

    # Custom labels (empty string means use default)
    custom_label = cfg.get('custom_label', '')
    custom_xlabel = cfg.get('custom_xlabel', '')
    custom_ylabel = cfg.get('custom_ylabel', '')

    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_type == "Bar":
        if y_col == "Count" or y_col is None:
            counts = plot_df[x_col].value_counts()
            if use_others and len(counts) > top_n:
                top = counts.head(top_n)
                others = counts.iloc[top_n:].sum()
                counts = pd.concat([top, pd.Series({'Others': others})])
            else:
                counts = counts.head(top_n)
            if sort_by == "Alphabetical":
                counts = counts.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                counts = counts.sort_values(ascending=(sort_order == "Ascending"))
            counts.plot(kind='bar', ax=ax, color=sns.color_palette(selected_palette or "pastel", len(counts)))
        else:
            grouped = plot_df.groupby(x_col)[y_col].sum()
            if use_others and len(grouped) > top_n:
                top = grouped.sort_values(ascending=False).head(top_n)
                others = grouped.iloc[top_n:].sum()
                grouped = pd.concat([top, pd.Series({'Others': others})])
            else:
                grouped = grouped.sort_values(ascending=False).head(top_n)
            if sort_by == "Alphabetical":
                grouped = grouped.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                grouped = grouped.sort_values(ascending=(sort_order == "Ascending"))
            grouped.plot(kind='bar', ax=ax, color=sns.color_palette(selected_palette or "pastel", len(grouped)))

        # Custom labels with fallback
        default_xlabel = x_col.replace('_', ' ').title()
        default_ylabel = y_col.replace('_', ' ').title() if y_col else "Count"
        default_title = f"{x_col.replace('_', ' ').title()} by {y_col.replace('_', ' ').title() if y_col and y_col != 'Count' else 'Count'}"
        ax.set_xlabel(custom_xlabel if custom_xlabel else default_xlabel)
        ax.set_ylabel(custom_ylabel if custom_ylabel else default_ylabel)
        ax.set_title(custom_label if custom_label else default_title)
        plt.xticks(rotation=45, ha='right')

    elif chart_type == "Horizontal Bar":
        if y_col == "Count" or y_col is None:
            counts = plot_df[x_col].value_counts()
            if use_others and len(counts) > top_n:
                top = counts.head(top_n)
                others = counts.iloc[top_n:].sum()
                counts = pd.concat([top, pd.Series({'Others': others})])
            else:
                counts = counts.head(top_n)
            if sort_by == "Alphabetical":
                counts = counts.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                counts = counts.sort_values(ascending=(sort_order == "Ascending"))
            counts.plot(kind='barh', ax=ax, color=sns.color_palette(selected_palette or "summer", len(counts)))
        else:
            grouped = plot_df.groupby(x_col)[y_col].sum()
            if use_others and len(grouped) > top_n:
                top = grouped.sort_values(ascending=True).tail(top_n)
                others = grouped.iloc[:-top_n].sum()
                grouped = pd.concat([pd.Series({'Others': others}), top])
            else:
                grouped = grouped.sort_values(ascending=True).tail(top_n)
            if sort_by == "Alphabetical":
                grouped = grouped.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                grouped = grouped.sort_values(ascending=(sort_order == "Ascending"))
            grouped.plot(kind='barh', ax=ax, color=sns.color_palette(selected_palette or "summer", len(grouped)))

        default_xlabel = y_col.replace('_', ' ').title() if y_col else "Count"
        default_ylabel = x_col.replace('_', ' ').title()
        default_title = f"{x_col.replace('_', ' ').title()} by {y_col.replace('_', ' ').title() if y_col and y_col != 'Count' else 'Count'}"
        ax.set_xlabel(custom_xlabel if custom_xlabel else default_xlabel)
        ax.set_ylabel(custom_ylabel if custom_ylabel else default_ylabel)
        ax.set_title(custom_label if custom_label else default_title)

    elif chart_type == "Pie":
        counts = plot_df[x_col].value_counts()
        if use_others and len(counts) > top_n:
            top = counts.head(top_n)
            others = counts.iloc[top_n:].sum()
            counts = pd.concat([top, pd.Series({'Others': others})])
        else:
            counts = counts.head(top_n)
        if sort_by == "Alphabetical":
            counts = counts.sort_index(ascending=(sort_order == "Ascending"))
        elif sort_by in ["Count / Value", "Value"]:
            counts = counts.sort_values(ascending=(sort_order == "Ascending"))
        counts.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90,
                    colors=sns.color_palette(selected_palette or "pastel", len(counts)))
        ax.set_ylabel("")
        default_title = f"{x_col.replace('_', ' ').title()} Distribution"
        ax.set_title(custom_label if custom_label else default_title)

    elif chart_type == "Histogram":
        if plot_df[x_col].dtype in ['int64', 'float64']:
            ax.hist(plot_df[x_col], bins=30, color='steelblue', edgecolor='white', alpha=0.8)
            default_xlabel = x_col.replace('_', ' ').title()
            default_ylabel = "Frequency"
            default_title = f"Distribution of {x_col.replace('_', ' ').title()}"
            ax.set_xlabel(custom_xlabel if custom_xlabel else default_xlabel)
            ax.set_ylabel(custom_ylabel if custom_ylabel else default_ylabel)
            ax.set_title(custom_label if custom_label else default_title)
        else:
            counts = plot_df[x_col].value_counts()
            if use_others and len(counts) > top_n:
                top = counts.head(top_n)
                others = counts.iloc[top_n:].sum()
                counts = pd.concat([top, pd.Series({'Others': others})])
            else:
                counts = counts.head(top_n)
            if sort_by == "Alphabetical":
                counts = counts.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                counts = counts.sort_values(ascending=(sort_order == "Ascending"))
            counts.plot(kind='bar', ax=ax, color=sns.color_palette(selected_palette or "pastel", len(counts)))
            default_xlabel = x_col.replace('_', ' ').title()
            default_ylabel = "Count"
            default_title = f"{x_col.replace('_', ' ').title()} Distribution"
            ax.set_xlabel(custom_xlabel if custom_xlabel else default_xlabel)
            ax.set_ylabel(custom_ylabel if custom_ylabel else default_ylabel)
            ax.set_title(custom_label if custom_label else default_title)
            plt.xticks(rotation=45, ha='right')

    elif chart_type == "Box Plot":
        if y_col and y_col != "Count":
            sns.boxplot(data=plot_df, x=x_col, y=y_col, ax=ax, palette=selected_palette)
            plt.xticks(rotation=45, ha='right')
            default_title = f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}"
            ax.set_title(custom_label if custom_label else default_title)
            # xlabel/ylabel are set by seaborn, but we can override
            if custom_xlabel:
                ax.set_xlabel(custom_xlabel)
            if custom_ylabel:
                ax.set_ylabel(custom_ylabel)
        else:
            ax.text(0.5, 0.5, "Box Plot needs a numeric Y axis", ha='center', va='center', transform=ax.transAxes)

    elif chart_type == "Line":
        if y_col == "Count":
            counts = plot_df[x_col].value_counts()
            if use_others and len(counts) > top_n:
                top = counts.head(top_n)
                others = counts.iloc[top_n:].sum()
                counts = pd.concat([top, pd.Series({'Others': others})])
            else:
                counts = counts.head(top_n)
            if sort_by == "Alphabetical":
                counts = counts.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                counts = counts.sort_values(ascending=(sort_order == "Ascending"))
            counts.plot(kind='line', ax=ax, marker='o', color='steelblue')
        else:
            grouped = plot_df.groupby(x_col)[y_col].sum()
            if use_others and len(grouped) > top_n:
                top = grouped.head(top_n)
                others = grouped.iloc[top_n:].sum()
                grouped = pd.concat([top, pd.Series({'Others': others})])
            else:
                grouped = grouped.head(top_n)
            if sort_by == "Alphabetical":
                grouped = grouped.sort_index(ascending=(sort_order == "Ascending"))
            elif sort_by in ["Count / Value", "Value"]:
                grouped = grouped.sort_values(ascending=(sort_order == "Ascending"))
            grouped.plot(kind='line', ax=ax, marker='o', color='steelblue')

        default_xlabel = x_col.replace('_', ' ').title()
        default_ylabel = y_col.replace('_', ' ').title() if y_col else "Count"
        default_title = f"{x_col.replace('_', ' ').title()} Trend by {y_col.replace('_', ' ').title() if y_col and y_col != 'Count' else 'Count'}"
        ax.set_xlabel(custom_xlabel if custom_xlabel else default_xlabel)
        ax.set_ylabel(custom_ylabel if custom_ylabel else default_ylabel)
        ax.set_title(custom_label if custom_label else default_title)
        plt.xticks(rotation=45, ha='right')

    elif chart_type == "Correlation Heatmap":
        if selected_cols and len(selected_cols) >= 2:
            corr_df = pd.DataFrame()
            for col in selected_cols:
                if plot_df[col].dtype in ['int64', 'float64']:
                    corr_df[col] = plot_df[col]
                else:
                    corr_df[col] = pd.Categorical(plot_df[col]).codes
            corr = corr_df[selected_cols].corr()
            sns.heatmap(corr, annot=True, fmt='.2f', cmap=selected_palette or 'RdBu_r',
                        center=0, ax=ax, square=True, linewidths=0.5)
            default_title = "Correlation Matrix"
            ax.set_title(custom_label if custom_label else default_title)
        else:
            ax.text(0.5, 0.5, "Select at least 2 columns", ha='center', va='center', transform=ax.transAxes)

    elif chart_type == "Category Heatmap":
        if x_col and y_col:
            pivot = plot_df.groupby([y_col, x_col]).size().unstack(fill_value=0)
            sns.heatmap(pivot, annot=True, fmt='d', cmap=selected_palette or 'YlOrRd', ax=ax)
            default_title = f"{x_col.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}"
            ax.set_title(custom_label if custom_label else default_title)
        else:
            ax.text(0.5, 0.5, "Need 2 categorical columns", ha='center', va='center', transform=ax.transAxes)

    plt.tight_layout()
    return fig


# ============================================================
# UPLOAD
# ============================================================
st.sidebar.title("📊 ChartGrid")

if st.session_state.loaded:
    st.sidebar.success(f"✅ {st.session_state.filename}")
    st.sidebar.info(f"{len(st.session_state.df):,} rows × {len(st.session_state.df.columns)} cols")
    if st.sidebar.button("🗑️ Clear All"):
        reset()
        st.rerun()
else:
    f = st.sidebar.file_uploader("Upload CSV", type=['csv'])
    if f:
        try:
            try:
                df = pd.read_csv(f, encoding='utf-8')
            except:
                f.seek(0)
                df = pd.read_csv(f, encoding='latin-1')

            df.columns = [str(c).strip().lower().replace(' ', '_').replace('-', '_') for c in df.columns]
            df = df.loc[:, ~df.columns.str.contains('^unnamed')]

            for c in df.columns:
                if df[c].dtype == 'object':
                    df[c] = df[c].fillna('Unknown')
                elif df[c].dtype in ['int64', 'float64']:
                    df[c] = df[c].fillna(0)

            st.session_state.df = df
            st.session_state.loaded = True
            st.session_state.filename = f.name
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
            st.error("Could not read file. Save as CSV UTF-8 and retry.")
    else:
        st.info("👈 Upload a CSV to get started.")
        st.markdown("""
        ### 📊 ChartGrid

        1. Upload any cleaned CSV dataset
        2. Add charts with the sidebar form
        3. Edit existing charts from the dropdown
        4. Universal filters apply to ALL charts at once
        5. Drag and resize charts in the grid
        """)
        st.stop()


df = st.session_state.df
num_cols = [c for c in df.columns if df[c].dtype in ['int64', 'float64']]
cat_cols = [c for c in df.columns if df[c].dtype == 'object']

st.title("📊 ChartGrid")
st.markdown(f"**{st.session_state.filename}** · {len(df):,} rows × {len(df.columns)} columns")


# ============================================================
# DATA TABLE
# ============================================================
with st.expander("📋 View Data Table", expanded=True):
    search = st.text_input("🔍 Search:", "")
    if search:
        mask = False
        for c in df.columns:
            if df[c].dtype == 'object':
                mask = mask | df[c].astype(str).str.contains(search, case=False, na=False)
        st.dataframe(df[mask], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, st.session_state.filename, "text/csv")


# ============================================================
# SIDEBAR: CHART EDITOR & UNIVERSAL FILTERS
# ============================================================
st.sidebar.markdown("---")

# --- Chart Selector (Edit existing) ---
if st.session_state.charts:
    st.sidebar.header("✏️ Edit Chart")
    chart_options = {f"Chart #{c['id']} — {c['type']}": c['id'] for c in st.session_state.charts}
    selected_chart_label = st.sidebar.selectbox(
        "Select chart to edit",
        ["None"] + list(chart_options.keys()),
        key="edit_chart_selector"
    )

    if selected_chart_label != "None":
        st.session_state.edit_chart_id = chart_options[selected_chart_label]
    else:
        st.session_state.edit_chart_id = None
else:
    st.session_state.edit_chart_id = None

# --- Universal Filters (apply to ALL charts) ---
st.sidebar.markdown("---")
st.sidebar.header("🌍 Universal Filters")
st.sidebar.caption("These apply to ALL charts simultaneously")

univ_top_n = st.sidebar.slider("Top N", 5, 50, 15, key="univ_top_n")
univ_others = st.sidebar.toggle("📦 Group as 'Others'", value=False, key="univ_others")
univ_sort_by = st.sidebar.selectbox("Sort by", ["Default", "Count / Value", "Alphabetical"], key="univ_sort")
univ_sort_order = st.sidebar.selectbox("Order", ["Descending", "Ascending"], key="univ_order")

# Apply universal filters to all chart configs
for c in st.session_state.charts:
    c['top_n'] = univ_top_n
    c['use_others'] = univ_others
    c['sort_by'] = univ_sort_by
    c['sort_order'] = univ_sort_order

# --- Add / Edit Chart Form ---
st.sidebar.markdown("---")
st.sidebar.header("➕ Add / Edit Chart")

# If editing, load existing config
edit_cfg = None
if st.session_state.edit_chart_id:
    edit_cfg = next((c for c in st.session_state.charts if c['id'] == st.session_state.edit_chart_id), None)

# Chart type selector outside form so conditional fields update immediately
chart_type_options = ["Bar", "Horizontal Bar", "Pie", "Histogram", "Box Plot", "Line",
                      "Correlation Heatmap", "Category Heatmap"]
chart_type = st.sidebar.selectbox(
    "Chart Type",
    chart_type_options,
    index=chart_type_options.index(edit_cfg['type']) if edit_cfg else 0,
    key="form_chart_type"
)

x_col = None
y_col = None
selected_cols = None

with st.sidebar.form("chart_form"):
    if chart_type == "Correlation Heatmap":
        all_available = list(df.columns)
        default_sel = edit_cfg['selected_cols'] if edit_cfg else (num_cols[:4] if len(num_cols) >= 2 else all_available[:min(4, len(all_available))])
        selected_cols = st.multiselect("Columns to Measure", all_available, default=default_sel)
        if selected_cols:
            x_col = selected_cols[0] if len(selected_cols) > 0 else None
            y_col = selected_cols[1] if len(selected_cols) > 1 else selected_cols[0] if len(selected_cols) > 0 else None

    elif chart_type == "Category Heatmap":
        if len(cat_cols) >= 2:
            x_col = st.selectbox("X Category", cat_cols,
                                 index=cat_cols.index(edit_cfg['x']) if edit_cfg and edit_cfg['x'] in cat_cols else 0,
                                 key="form_heat_x")
            y_options = [c for c in cat_cols if c != x_col]
            y_col = st.selectbox("Y Category", y_options,
                                 index=y_options.index(edit_cfg['y']) if edit_cfg and edit_cfg['y'] in y_options else 0,
                                 key="form_heat_y") if y_options else None
        else:
            st.warning("Need 2+ categorical columns")

    else:
        x_col = st.selectbox("X Axis", df.columns,
                            index=list(df.columns).index(edit_cfg['x']) if edit_cfg and edit_cfg['x'] in df.columns else 0,
                            key="form_x")
        if chart_type in ["Bar", "Horizontal Bar", "Line", "Box Plot"]:
            y_options = ["Count"] + num_cols
            y_col = st.selectbox("Y Axis", y_options,
                                index=y_options.index(edit_cfg['y']) if edit_cfg and edit_cfg['y'] in y_options else 0,
                                key="form_y")

    color = st.selectbox("Color", ["Default", "Summer", "Set1", "Set2", "Set3", "Pastel", "Dark",
                                    "Blues", "Greens", "Oranges", "RdBu_r", "YlOrRd", "coolwarm"],
                         index=["Default", "Summer", "Set1", "Set2", "Set3", "Pastel", "Dark",
                                "Blues", "Greens", "Oranges", "RdBu_r", "YlOrRd", "coolwarm"].index(edit_cfg['color']) if edit_cfg else 0)

    # Custom Labels Section
    st.markdown("---")
    st.markdown("**✏️ Custom Labels** *(leave empty for auto-generated)*")
    custom_label = st.text_input("Chart Title", value=edit_cfg.get('custom_label', '') if edit_cfg else '', key="form_custom_label")
    custom_xlabel = st.text_input("X-Axis Label", value=edit_cfg.get('custom_xlabel', '') if edit_cfg else '', key="form_custom_xlabel")
    custom_ylabel = st.text_input("Y-Axis Label", value=edit_cfg.get('custom_ylabel', '') if edit_cfg else '', key="form_custom_ylabel")

    # Chart-specific filters
    st.markdown("---")
    st.markdown("**Chart Filters**")
    chart_filters = {}
    for i, col in enumerate(cat_cols[:3]):
        vals = ['All'] + sorted(df[col].dropna().unique().tolist())
        default_val = edit_cfg['filters'].get(col, 'All') if edit_cfg else 'All'
        chart_filters[col] = st.selectbox(f"Filter {col.replace('_', ' ').title()}", vals,
                                          index=vals.index(default_val) if default_val in vals else 0,
                                          key=f"form_filt_{i}")

    submitted = st.form_submit_button("💾 Save Chart" if edit_cfg else "➕ Add Chart", type="primary")

    if submitted:
        new_cfg = {
            'id': edit_cfg['id'] if edit_cfg else st.session_state.chart_counter + 1,
            'type': chart_type,
            'x': x_col,
            'y': y_col,
            'selected_cols': selected_cols,
            'top_n': univ_top_n,
            'color': color,
            'use_others': univ_others,
            'sort_by': univ_sort_by,
            'sort_order': univ_sort_order,
            'filters': {k: v for k, v in chart_filters.items() if v != 'All'},
            'custom_label': custom_label.strip(),
            'custom_xlabel': custom_xlabel.strip(),
            'custom_ylabel': custom_ylabel.strip()
        }

        if edit_cfg:
            idx = next(i for i, c in enumerate(st.session_state.charts) if c['id'] == edit_cfg['id'])
            st.session_state.charts[idx] = new_cfg
        else:
            st.session_state.chart_counter += 1
            st.session_state.charts.append(new_cfg)

        st.rerun()

# Delete button for selected chart
if st.session_state.edit_chart_id:
    if st.sidebar.button("🗑️ Delete Selected Chart", type="secondary"):
        st.session_state.charts = [c for c in st.session_state.charts if c['id'] != st.session_state.edit_chart_id]
        st.session_state.edit_chart_id = None
        st.session_state.layout = None
        st.rerun()


# ============================================================
# RENDER DASHBOARD
# ============================================================
st.markdown("---")

if not st.session_state.charts:
    st.info("👈 Use the sidebar to add your first chart!")
    st.session_state.edit_chart_id = None
else:
    palette_map = {
        "Default": None, "Summer": "summer", "Set1": "Set1", "Set2": "Set2",
        "Set3": "Set3", "Pastel": "pastel", "Dark": "dark",
        "Blues": "Blues", "Greens": "Greens", "Oranges": "Oranges",
        "RdBu_r": "RdBu_r", "YlOrRd": "YlOrRd", "coolwarm": "coolwarm"
    }

    # Clean up stale edit_chart_id if chart no longer exists
    if st.session_state.edit_chart_id is not None:
        if not any(c['id'] == st.session_state.edit_chart_id for c in st.session_state.charts):
            st.session_state.edit_chart_id = None
            st.rerun()

    # Try to use streamlit-elements for draggable grid
    try:
        from streamlit_elements import elements, dashboard, mui, html

        # Build layout if not exists or if charts changed
        current_ids = {c['id'] for c in st.session_state.charts}
        layout_ids = {item['i'].replace('chart_', '') for item in st.session_state.layout} if st.session_state.layout else set()

        if st.session_state.layout is None or current_ids != layout_ids:
            st.session_state.layout = [
                dashboard.Item(f"chart_{c['id']}", (i % 2) * 6, (i // 2) * 4, 6, 4)
                for i, c in enumerate(st.session_state.charts)
            ]

        def handle_layout_change(updated_layout):
            st.session_state.layout = updated_layout

        with elements("dashboard"):
            with dashboard.Grid(st.session_state.layout, onLayoutChange=handle_layout_change, draggableHandle=".draggable"):
                for cfg in st.session_state.charts:
                    # Apply chart-specific filters
                    plot_df = df.copy()
                    for col, val in cfg['filters'].items():
                        plot_df = plot_df[plot_df[col] == val]

                    # Render chart
                    fig = render_chart(cfg, plot_df, palette_map)
                    img_b64 = fig_to_base64(fig)

                    with mui.Card(key=f"chart_{cfg['id']}", sx={"display": "flex", "flexDirection": "column"}):
                        with mui.Box(sx={"display": "flex", "alignItems": "center", "backgroundColor": "#f5f5f5", "padding": "8px 12px"}):
                            mui.Typography(
                                f"Chart #{cfg['id']} — {cfg['type']}",
                                sx={"flex": 1, "fontWeight": 500, "cursor": "move"},
                                className="draggable"
                            )
                        with mui.CardContent(sx={"flex": 1, "minHeight": 0, "padding": "8px"}):
                            html.img(
                                src=f"data:image/png;base64,{img_b64}",
                                css={"width": "100%", "height": "100%", "objectFit": "contain"}
                            )

    except ImportError:
        # Fallback: static grid layout
        st.info("💡 Install `streamlit-elements` for drag-and-resize: `pip install streamlit-elements==0.1.*`")

        cols = st.columns(2)
        for i, cfg in enumerate(st.session_state.charts):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"**Chart #{cfg['id']} — {cfg['type']}**")

                    # Show filters
                    if cfg['filters']:
                        filter_text = " | ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in cfg['filters'].items()])
                        st.caption(f"🔍 {filter_text}")

                    # Apply chart-specific filters
                    plot_df = df.copy()
                    for col, val in cfg['filters'].items():
                        plot_df = plot_df[plot_df[col] == val]

                    # Render chart
                    fig = render_chart(cfg, plot_df, palette_map)
                    st.pyplot(fig)
                    plt.close()

st.markdown("---")
st.caption("ChartGrid v4.3 | Multi-Chart | Session-only | Custom Labels")