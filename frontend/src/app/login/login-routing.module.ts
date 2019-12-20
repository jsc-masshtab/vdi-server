
import { LoginComponent } from './login.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)], // <-- debugging purposes only { enableTracing: true }
  exports: [RouterModule]
})


export class LoginRoutingModule {}
