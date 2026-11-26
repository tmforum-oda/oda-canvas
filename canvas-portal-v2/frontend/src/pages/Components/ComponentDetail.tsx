import { useParams, useNavigate } from 'react-router-dom'
import ComponentDetailBody from './ComponentDetailBody'

// Standalone deep-link route. The default UX is the master-detail drawer
// rendered by Components/index.tsx; this kept around for direct navigation.
export default function ComponentDetail() {
  const { namespace = '', name = '' } = useParams<{ namespace: string; name: string }>()
  const navigate = useNavigate()
  return (
    <ComponentDetailBody
      namespace={namespace}
      name={name}
      onClose={() => navigate('/components')}
    />
  )
}
