import { Button } from '@mui/material';
import PropTypes from 'prop-types';
import Footer from './Footer';
import PersistentDrawerLeft from './menu'



// ==============================|| MINIMAL LAYOUT ||============================== //

const MinimalLayout = ({ children }) => (
    <>
    <PersistentDrawerLeft />
    {children}
    <Footer />
  </>
);

MinimalLayout.propTypes = {
  children: PropTypes.node
};

export default MinimalLayout;
