import { lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import { AuthProvider } from "./context/AuthProvider";
import { FavoritesProvider } from "./context/FavoritesProvider";
import { SearchDraftProvider } from "./context/SearchDraftProvider";
import Home from "./pages/Home";

// Lazy loaded routes
const SearchResultsPage = lazy(() => import("./pages/SearchResults"));
const Products = lazy(() => import("./pages/Products"));
const ProductDetailsPage = lazy(() => import("./pages/ProductDetails"));
const Favorites = lazy(() => import("./pages/Favorites"));
const About = lazy(() => import("./pages/About"));
const Login = lazy(() => import("./pages/Login"));
const OwnerEnquiries = lazy(() => import("./pages/OwnerEnquiries"));
const CustomerEnquiries = lazy(() => import("./pages/CustomerEnquiries"));
const NotFound = lazy(() => import("./pages/NotFound"));

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <FavoritesProvider>
          <SearchDraftProvider>
            <Routes>
              <Route element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="login" element={<Login />} />
                <Route path="search" element={<SearchResultsPage />} />
                <Route path="products" element={<Products />} />
                <Route path="products/:id" element={<ProductDetailsPage />} />
                <Route path="favorites" element={<Favorites />} />
                <Route path="about" element={<About />} />
                <Route path="owner/enquiries" element={<OwnerEnquiries />} />
                <Route path="my-enquiries" element={<CustomerEnquiries />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </SearchDraftProvider>
        </FavoritesProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
