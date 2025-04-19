// Mock for react-router-dom
export const useNavigate = jest.fn();
export const useParams = jest.fn().mockReturnValue({});
export const Link = ({ to, children }: { to: string; children: React.ReactNode }) => 
  <a href={to}>{children}</a>;
export const Routes = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const Route = () => <div />;
export const BrowserRouter = ({ children }: { children: React.ReactNode }) => <>{children}</>;
export const Outlet = () => <div data-testid="outlet" />;
export const Navigate = () => <div />;