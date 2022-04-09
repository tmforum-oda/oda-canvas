import { Button } from '@mui/material';
import PropTypes from 'prop-types';
import PersistentDrawerLeft from './menu'



// ==============================|| MINIMAL LAYOUT ||============================== //

const MinimalLayout = ({ children }) => (
    <>
    <PersistentDrawerLeft></PersistentDrawerLeft>
    {children}
  </>
);

MinimalLayout.propTypes = {
  children: PropTypes.node
};

export default MinimalLayout;
