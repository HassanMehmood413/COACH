import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const data = [
  { name: "Mon", conversations: 4 },
  { name: "Tue", conversations: 3 },
  { name: "Wed", conversations: 7 },
  { name: "Thu", conversations: 5 },
  { name: "Fri", conversations: 6 },
  { name: "Sat", conversations: 4 },
  { name: "Sun", conversations: 8 },
]

export function Analytics() {
  return (
    <Card className="h-[calc(100vh-8rem)]">
      <CardHeader>
        <CardTitle>Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="conversations" stroke="hsl(var(--primary))" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

