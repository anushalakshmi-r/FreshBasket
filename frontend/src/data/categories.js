const image = (id) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=480&q=80`

export const categories = [
  { id: 'vegetables', name: 'Vegetables', image: image('photo-1540420773420-3366772f4999') },
  { id: 'fruits', name: 'Fruits', image: image('photo-1610832958506-aa56368176cf') },
  { id: 'dairy-eggs', name: 'Dairy & Eggs', image: image('photo-1550583724-b2692b85b150') },
  { id: 'rice-pulses', name: 'Rice & Pulses', image: image('photo-1586201375761-83865001e31c') },
  { id: 'meat-seafood', name: 'Meat & Seafood', image: image('photo-1607623814075-e51df1bdc82f') },
  { id: 'fish-prawns', name: 'Fish & Prawns', image: image('photo-1519708227418-c8fd9a32b7a2') },
  { id: 'bakery', name: 'Bakery', image: image('photo-1509440159596-0249088772ff') },
  { id: 'snacks', name: 'Snacks', image: image('photo-1508061253366-f7da158b6d46') },
  { id: 'beverages', name: 'Beverages', image: image('photo-1544145945-f90425340c7e') },
  { id: 'cooking-oils', name: 'Cooking Oils', image: image('photo-1474979266404-7eaacbcd87c5') },
  { id: 'masala-spices', name: 'Masala & Spices', image: image('photo-1596040033229-a9821ebd058d') },
  { id: 'personal-care', name: 'Personal Care', image: image('photo-1608248543803-ba4f8c70ae0b') },
  { id: 'household-essentials', name: 'Household Essentials', image: image('photo-1558618666-fcd25c85cd64') },
  { id: 'baby-care', name: 'Baby Care', image: image('photo-1519689680058-324335c77eba') },
  { id: 'frozen-foods', name: 'Frozen Foods', image: image('photo-1490645935967-10de6ba17061') },
  { id: 'organic-foods', name: 'Organic Foods', image: image('photo-1540420773420-3366772f4999') },
  { id: 'pet-care', name: 'Pet Care', image: image('photo-1589924691995-400dc9ecc119') },
  { id: 'home-kitchen', name: 'Home & Kitchen', image: image('photo-1556911220-bff31c812dba') },
  { id: 'pooja-essentials', name: 'Pooja Essentials', image: image('photo-1490750967868-88aa4486c946') },
  { id: 'stationery', name: 'Stationery', image: image('photo-1455390582262-044cdead277a') },
]
