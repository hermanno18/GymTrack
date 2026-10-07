declare module '#auth-utils' {
  interface User {
    id: number
    email: string
    weightUnit: 'kg' | 'lb'
    distanceUnit: 'km' | 'mi'
  }
}

export {}
