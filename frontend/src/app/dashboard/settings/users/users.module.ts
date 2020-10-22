import { AddUserComponent } from './add-user/add-user.component';
import { UsersComponent } from './all-users/users.component';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { UsersService } from './users.service';
import { UserDetailsComponent } from './user-details/user-details.component';
import { MatCheckboxModule, MatInputModule } from '@angular/material';
import { MutateUserComponent } from './user-details/mutate-user/mutate-user.component';
import { AddGropComponent } from './user-details/add-group/add-group.component';
import { AddRoleComponent } from './user-details/add-role/add-role.component'; 
import { RemoveRoleComponent } from './user-details/remove-role/remove-role.component';
import { RemoveGroupComponent } from './user-details/remove-group/remove-group.component';

@NgModule({
   declarations: [
      UsersComponent,
      AddUserComponent,
      AddGropComponent,
      AddRoleComponent,
      UserDetailsComponent,
      MutateUserComponent,
      RemoveRoleComponent,
      RemoveGroupComponent
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
      MatInputModule
   ],
   providers: [
      UsersService
   ],
   exports: [
      UsersComponent
   ],
   entryComponents: [
      AddUserComponent,
      AddGropComponent,
      AddRoleComponent,
      MutateUserComponent,
      RemoveRoleComponent,
      RemoveGroupComponent
   ]
})
export class UsersModule { }
