import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgxQRCodeModule } from '@techiediaries/ngx-qrcode';
import { AppRoutingModule } from 'app/app-routing.module';
import { GenerateQrcodeComponent } from 'app/dashboard/settings/users/user-details/generate-qrcode/generate-qrcode.component';

import { SharedModule } from '@shared/shared.module';

import { AddUserComponent } from './add-user/add-user.component';
import { UsersComponent } from './all-users/users.component';
import { AddGropComponent } from './user-details/add-group/add-group.component';
import { AddPermissionComponent } from './user-details/add-permission/add-permission.component';
import { AddRoleComponent } from './user-details/add-role/add-role.component'; 
import { MutateUserComponent } from './user-details/mutate-user/mutate-user.component';
import { RemoveGroupComponent } from './user-details/remove-group/remove-group.component';
import { RemovePermissionComponent } from './user-details/remove-permission/remove-permission.component';
import { RemoveRoleComponent } from './user-details/remove-role/remove-role.component';
import { UserDetailsComponent } from './user-details/user-details.component';
import { UsersService } from './users.service';


@NgModule({
   declarations: [
      UsersComponent,
      AddUserComponent,
      AddGropComponent,
      AddRoleComponent,
      AddPermissionComponent,
      UserDetailsComponent,
      MutateUserComponent,
      RemoveRoleComponent,
      RemoveGroupComponent,
      RemovePermissionComponent,
      GenerateQrcodeComponent
   ],
   imports: [
      SharedModule,
      CommonModule,
      FontAwesomeModule,
      AppRoutingModule,
      MatDialogModule,
      MatSelectModule,
      ReactiveFormsModule,
      MatCheckboxModule,
      MatInputModule,
      NgxQRCodeModule
   ],
   providers: [
      UsersService
   ],
   exports: [
      UsersComponent
   ]
})
export class UsersModule { }
