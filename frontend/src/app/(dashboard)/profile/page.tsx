import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { ROLE_LABELS } from "@/lib/labels";
import { getMe } from "@/lib/queries";

import { AvatarForm } from "./AvatarForm";
import { ChangePasswordForm } from "./ChangePasswordForm";
import { ProfileForm } from "./ProfileForm";

export default async function ProfilePage() {
  const me = await getMe();

  return (
    <>
      <PageHeader title="Mi perfil" subtitle={me.email} />

      <InfoBanner>
        Actualiza tu nombre visible y cambia tu contraseña. Para cambiarla debes
        confirmar tu contraseña actual; si la olvidaste, pide a un administrador que la
        restablezca.
      </InfoBanner>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Datos</h2>
          <div className="card space-y-4">
            <AvatarForm currentAvatar={me.avatar_url} />
            <hr className="border-brand-50" />
            <div>
              <p className="label">Correo</p>
              <p className="text-sm text-slate-700">{me.email}</p>
            </div>
            <div>
              <p className="label">Rol</p>
              <p className="text-sm text-slate-700">{ROLE_LABELS[me.role]}</p>
            </div>
            <hr className="border-brand-50" />
            <ProfileForm currentName={me.full_name} />
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-slate-800">
            Cambiar contraseña
          </h2>
          <div className="card">
            <ChangePasswordForm />
          </div>
        </section>
      </div>
    </>
  );
}
