# Investor Ops Intelligence Suite — UI Guidelines

> Copy this file into your Cursor project. These guidelines define every visual and structural decision made in this app. Follow them exactly when building new pages, components, or features.

---

## 1. Stack

| Layer | Technology |
|---|---|
| Framework | React 19 + TypeScript + Vite |
| Styling | Tailwind CSS v4 (OKLCH color tokens) |
| Components | shadcn/ui — new-york style |
| Icons | Lucide React |
| Database | Supabase (supabase-js v2) |
| Animation | tw-animate-css |

---

## 2. Color System

All colors use CSS custom properties (OKLCH). **Never use raw hex or RGB values.** Always use Tailwind semantic utilities.

### Semantic Token → Tailwind Utility Map

| Token | Utility | Use |
|---|---|---|
| `--background` | `bg-background` | Page background |
| `--foreground` | `text-foreground` | Primary text |
| `--card` | `bg-card` | Card surfaces |
| `--card-foreground` | `text-card-foreground` | Text on cards |
| `--primary` | `bg-primary` | Brand black, CTA buttons, active states |
| `--primary-foreground` | `text-primary-foreground` | Text on primary |
| `--muted` | `bg-muted` | Subtle backgrounds, input fills |
| `--muted-foreground` | `text-muted-foreground` | Secondary labels, hints |
| `--border` | `border-border` | All borders |
| `--destructive` | `bg-destructive` | Errors, rejections, losers |
| `--sidebar` | `bg-sidebar` | Sidebar background |
| `--sidebar-foreground` | `text-sidebar-foreground` | Sidebar text |
| `--sidebar-accent` | `bg-sidebar-accent` | Sidebar hover state |
| `--sidebar-border` | `border-sidebar-border` | Sidebar border |

### Semantic Status Colors (non-primary accents)

Always use these exact combinations. Never invent new color schemes.

| Semantic | Background | Text | Border | Use case |
|---|---|---|---|---|
| Success / Positive | `bg-emerald-50` | `text-emerald-700` | `border-emerald-200` | Gains, confirmed, approved, positive sentiment |
| Warning / Rescheduled | `bg-amber-50` | `text-amber-700` | `border-amber-200` | Pending, rescheduled, caution |
| Destructive / Negative | `bg-destructive/10` | `text-destructive` | `border-destructive/20` | Losses, cancelled, rejected, errors |
| Info / Blue | `bg-blue-50` | `text-blue-600` | — | Calendar, login, neutral info icons |
| Sky / Teal | `bg-sky-50` | `text-sky-600` | — | Email, communications |
| Amber / Orange | `bg-amber-50` | `text-amber-600` | — | Voice, warnings |

### Icon Container Colors (KPI cards, list item icons)

```tsx
// Always pair these icon container classes with icon classes
"bg-blue-50 text-blue-600"       // login, calendar, info
"bg-emerald-50 text-emerald-600" // success, chatbot, confirmed
"bg-amber-50 text-amber-600"     // voice, warnings
"bg-sky-50 text-sky-600"         // email
"bg-primary/10 text-primary"     // primary brand actions
"bg-destructive/10 text-destructive" // errors, pending high-priority
"bg-teal-50 text-teal-600"       // resources, books
```

---

## 3. Typography

No custom font — use system Inter/Geist stack. Use these exact class patterns:

```tsx
// Page titles (h2 level, each section)
"text-xl font-bold text-foreground"

// Section subtitles / descriptions
"text-sm text-muted-foreground mt-0.5"

// Card titles (CardTitle)
"text-sm font-semibold"  // always text-sm, not larger

// KPI metric numbers (large stat)
"text-2xl font-bold text-foreground leading-none"

// KPI labels (uppercase category label above metric)
"text-xs font-medium text-muted-foreground uppercase tracking-wider"

// Sub-labels below metrics
"text-xs text-muted-foreground"

// Trend indicators
"text-xs font-medium text-emerald-600"   // positive trend
"text-xs font-medium text-destructive"   // negative trend
"text-xs text-muted-foreground"          // neutral

// Table / list row primary text
"text-sm font-semibold text-foreground"

// Table / list row secondary text
"text-xs text-muted-foreground"

// Badge text
"text-xs"  // always text-xs inside Badge

// Navigation labels
"text-sm font-medium"

// Input placeholder text → inherited from Tailwind defaults
```

---

## 4. Spacing & Layout

### App Shell

```
┌─────────────────────────────────────────────────┐
│  Sidebar (w-64, fixed left, full height)        │
│  ┌─────────────────────────────────────────┐    │
│  │  Topbar (h-16, sticky, border-b)        │    │
│  │─────────────────────────────────────────│    │
│  │  <main> overflow-y-auto                 │    │
│  │    <div max-w-6xl mx-auto px-6 py-8>    │    │
│  │      [page content]                     │    │
│  │    </div>                               │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

```tsx
// Outer shell
<div className="flex h-screen overflow-hidden bg-background">
  <Sidebar />
  <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
    <Topbar />
    <main className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* page */}
      </div>
    </main>
  </div>
</div>
```

### Page-level spacing

```tsx
// Every page root
<div className="space-y-6">
  {/* header row */}
  {/* KPI row */}
  {/* content sections */}
</div>
```

### Grid patterns

```tsx
// 4-column KPI grid (desktop), 2-column (mobile)
<div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

// 2-column equal split
<div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

// 5-column with 3+2 split (main + sidebar widget)
<div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
  <div className="lg:col-span-3"> {/* main */} </div>
  <div className="lg:col-span-2"> {/* side */} </div>
</div>

// 3-column booking breakdown
<div className="grid grid-cols-3 gap-4">
```

---

## 5. Component Patterns

### KPI Card

```tsx
<Card className="border border-border shadow-sm hover:shadow-md transition-shadow">
  <CardContent className="pt-5 pb-5">
    <div className="flex items-start justify-between gap-3">
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider truncate">
          {label}
        </p>
        <p className="mt-1.5 text-2xl font-bold text-foreground leading-none">{value}</p>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
        {trendValue && (
          <div className="mt-2 flex items-center gap-1 text-xs font-medium text-emerald-600">
            <TrendingUp className="w-3 h-3" />
            {trendValue}
          </div>
        )}
      </div>
      <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-blue-50 text-blue-600">
        <Icon className="w-5 h-5" />
      </div>
    </div>
  </CardContent>
</Card>
```

### Section Card (data list, table, etc.)

```tsx
<Card className="border border-border">
  <CardHeader className="pb-3 flex flex-row items-center justify-between">
    <div>
      <CardTitle className="text-sm font-semibold">Title</CardTitle>
      <p className="text-xs text-muted-foreground mt-0.5">Subtitle</p>
    </div>
    <Button variant="ghost" size="sm" className="text-xs gap-1.5 h-8">
      Action <ArrowUpRight className="w-3 h-3" />
    </Button>
  </CardHeader>
  <CardContent className="pt-0">
    {/* content */}
  </CardContent>
</Card>
```

### Status Badges

```tsx
// Always use these exact patterns — never deviate
<Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs">Positive</Badge>
<Badge className="bg-amber-50 text-amber-700 border-amber-200 text-xs">Pending</Badge>
<Badge className="bg-destructive/10 text-destructive border-destructive/20 text-xs">Negative</Badge>
<Badge variant="secondary" className="text-xs">Neutral</Badge>
```

### Filter Pill Buttons (inline category filters)

```tsx
// Active state
"px-2.5 py-1 rounded-lg text-xs font-medium border bg-primary text-primary-foreground border-primary"

// Inactive state
"px-2.5 py-1 rounded-lg text-xs font-medium border bg-background text-muted-foreground border-border hover:border-primary/40"
```

### List Row (stock, fund, booking, etc.)

```tsx
<div className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
  <div className="flex items-center gap-3">
    <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
      <span className="text-[10px] font-bold text-muted-foreground">AB</span>
    </div>
    <div>
      <p className="text-sm font-semibold text-foreground">Label</p>
      <p className="text-xs text-muted-foreground">Sublabel</p>
    </div>
  </div>
  <div className="text-right">
    <p className="text-sm font-semibold text-foreground">Value</p>
    <p className="text-xs font-medium text-emerald-600">+1.24%</p>
  </div>
</div>
```

### Chat Bubble (RAG chatbot / voice agent)

```tsx
// User message (right-aligned, primary bg)
<div className="flex gap-3 flex-row-reverse">
  <div className="w-7 h-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0 mt-0.5">
    <User className="w-3.5 h-3.5" />
  </div>
  <div className="max-w-[78%] px-4 py-3 rounded-2xl rounded-tr-sm bg-primary text-primary-foreground text-sm leading-relaxed">
    {message}
  </div>
</div>

// Assistant message (left-aligned, muted bg)
<div className="flex gap-3 flex-row">
  <div className="w-7 h-7 rounded-full bg-muted text-muted-foreground flex items-center justify-center shrink-0 mt-0.5">
    <Bot className="w-3.5 h-3.5" />
  </div>
  <div className="max-w-[78%] px-4 py-3 rounded-2xl rounded-tl-sm bg-muted text-foreground text-sm leading-relaxed">
    {message}
  </div>
</div>
```

### Session Sidebar (chatbot / voice sessions, ChatGPT style)

```tsx
// Session item — active
"group flex items-center gap-2 px-3 py-2.5 rounded-lg bg-primary text-primary-foreground cursor-pointer"

// Session item — inactive
"group flex items-center gap-2 px-3 py-2.5 rounded-lg hover:bg-muted text-foreground cursor-pointer transition-all"

// Delete button inside session item (show on hover)
"opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:text-destructive text-muted-foreground"
```

### Approval / Action Row

```tsx
// Pending state — amber left border
<Card className="border border-border border-l-4 border-l-amber-400">

// Approve button (always green, not primary)
<Button className="bg-emerald-600 hover:bg-emerald-700 text-white">Approve</Button>

// Reject button
<Button variant="outline" className="border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground">Reject</Button>
```

### Scrape Status Indicator

```tsx
// Always shown near page header on data pages
<div className="flex items-center gap-2 mt-1">
  <Clock className="w-3.5 h-3.5 text-muted-foreground" />
  <span className="text-xs text-muted-foreground">Last scraped: May 6, 2026 · 10:42 AM</span>
  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
</div>
```

---

## 6. Sidebar

```tsx
// Sidebar shell
<aside className="flex flex-col w-64 shrink-0 bg-sidebar border-r border-sidebar-border h-screen sticky top-0">

// Logo block
<div className="px-5 py-5 border-b border-sidebar-border">
  <div className="flex items-center gap-2.5">
    <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
      <span className="text-primary-foreground text-xs font-bold">IO</span>
    </div>
    <div>
      <p className="text-sm font-semibold text-sidebar-foreground">App Name</p>
      <p className="text-xs text-muted-foreground">Tagline</p>
    </div>
  </div>
</div>

// Nav section label
<p className="px-3 mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">Navigation</p>

// Active nav item
"w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground shadow-sm"

// Inactive nav item
"w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-150"

// Nav icon size — always
<Icon className="w-4 h-4 shrink-0" />
```

---

## 7. Topbar

```tsx
<header className="h-16 bg-background border-b border-border flex items-center justify-between px-6 shrink-0 sticky top-0 z-30">
  {/* Left: app title + active page breadcrumb + live badge */}
  {/* Right: last-updated chip + notification bell + avatar */}
</header>

// Live status badge
<Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs font-medium flex items-center gap-1.5">
  <Wifi className="w-3 h-3" /> Active
</Badge>
```

---

## 8. Icon Sizing Convention

| Context | Size class |
|---|---|
| Nav items | `w-4 h-4` |
| KPI card icon (in container) | `w-5 h-5` |
| List row icon (small container) | `w-4 h-4` |
| Chat avatar icon | `w-3.5 h-3.5` |
| Badge / label icon | `w-3 h-3` |
| Trend indicator | `w-3 h-3` |
| Topbar bell | `w-4 h-4` |
| Page empty state | `w-8 h-8` |
| Voice agent hero mic | `w-8 h-8` |

---

## 9. Border Radius Convention

```
Rounded full (pill) → badges, status dots
rounded-full           → avatars, pulse dot, mic button
rounded-xl (0.75rem)   → cards (default Card), filter buttons, icon containers
rounded-lg (0.5rem)    → inputs, nav buttons, session items
rounded-2xl            → chat bubbles
rounded-lg             → small action buttons
```

Use `rounded-xl` for icon containers (12–16px), `rounded-lg` for interactive elements. Never use `rounded-3xl` or anything larger.

---

## 10. Shadow Convention

```
shadow-sm   → cards at rest (default Card)
shadow-md   → cards on hover
shadow-lg   → voice mic button active state
No shadow   → navigation items, inline badges, table rows
```

---

## 11. Tab Component Pattern

```tsx
<Tabs defaultValue="tab1">
  <TabsList className="h-9">
    <TabsTrigger value="tab1" className="text-xs">Tab One</TabsTrigger>
    <TabsTrigger value="tab2" className="text-xs">Tab Two</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1" className="mt-4">
    {/* content */}
  </TabsContent>
</Tabs>
```

Always `h-9` on TabsList, `text-xs` on TabsTrigger, `mt-4` on TabsContent.

---

## 12. Form & Input Patterns

```tsx
// Standard search input with icon
<div className="relative flex-1 min-w-48">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
  <Input className="pl-9 h-9 text-sm" placeholder="Search…" />
</div>

// Chat input row
<div className="flex gap-2">
  <Input className="flex-1 h-10 text-sm" placeholder="…" />
  <Button size="sm" className="h-10 w-10 p-0 shrink-0">
    <Send className="w-4 h-4" />
  </Button>
</div>

// Input heights: h-9 (filters/search), h-10 (chat/forms), h-11 (primary CTAs like login)
```

---

## 13. Progress Bar Usage

```tsx
// Always h-1.5, never larger in data-dense contexts
<Progress value={pct} className="h-1.5 flex-1" />

// Star rating bars
<Progress value={pct} className="h-1.5 w-20 shrink-0" />
```

---

## 14. Skeleton Loading States

```tsx
// Card skeleton
<Card className="border border-border">
  <CardContent className="pt-5 pb-5 space-y-2">
    <Skeleton className="h-3 w-24" />
    <Skeleton className="h-7 w-16" />
    <Skeleton className="h-3 w-32" />
  </CardContent>
</Card>

// List row skeleton
<Skeleton className="h-10 w-full rounded-xl" />

// Chat bubble skeleton
<Skeleton className="h-12 w-3/4 rounded-2xl" />
```

---

## 15. Live Indicator / Pulse Dot

```tsx
// Green pulse dot (used next to scrape timestamps)
<div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />

// Red live recording dot (voice agent active)
<span className="relative flex h-2.5 w-2.5">
  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
</span>
```

---

## 16. Role-Based Access Pattern

```tsx
const isAdmin = user?.role === "admin"

// Render admin-only nav items only when isAdmin
// Show "Admin" badge in sidebar: bg-primary/10 text-primary border-primary/20
// Show "Investor" badge: bg-muted text-muted-foreground border-border
```

---

## 17. Supabase Integration Conventions

```tsx
// Always use anon client (not authenticated) for this app's mock auth
import { createClient } from "@supabase/supabase-js"
export const supabase = createClient(VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY)

// Always maybeSingle() not single() for zero-or-one queries
const { data } = await supabase.from("table").select("*").eq("id", id).maybeSingle()

// Always log activity to activity_log after significant user actions
await supabase.from("activity_log").insert({
  user_id, user_name, event_type: "chatbot_used", metadata: { ... }
})

// RLS: all tables use anon-accessible policies (this is a mock-auth app)
```

---

## 18. What NOT to Do

- Never use raw hex values (`#1a1a1a`, `#fff`) — always use tokens
- Never use `text-gray-*`, `text-zinc-*` — use `text-foreground` or `text-muted-foreground`
- Never use `rounded-3xl` or larger
- Never make CardTitle larger than `text-sm`
- Never use `shadow-xl` or `shadow-2xl`
- Never add comments explaining what code does
- Never use purple, indigo, or violet hues
- Never add emojis to UI text
- Never create a new page without a `space-y-6` root wrapper
- Never use `single()` instead of `maybeSingle()` on Supabase queries
- Never skip RLS on new database tables
- Never hardcode user data — always pull from Supabase or mock context
