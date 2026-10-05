import GuestLayout from '../../layouts/GuestLayout.jsx'
import ScanPage from '../app/ScanPage.jsx'

export default function GuestScanPage() {
  return (
    <GuestLayout>
      <ScanPage guestMode />
    </GuestLayout>
  )
}
