import { RemoveGroupComponent } from './remove-groups/remove-group.component';
import { RemoveUserGroupComponent } from './groups-details/remove-user/remove-user.component';

import { AddGroupComponent } from './add-groups/add-groups.component';
import { GroupsComponent } from './all-groups/groups.component';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { AppRoutingModule } from '../../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

import { GroupsDetailsComponent } from './groups-details/groups-details.component';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatInputModule } from '@angular/material/input';
import { GroupsService } from './groups.service';
import { AddRoleComponent } from './groups-details/add-role/add-role.component';
import { RemoveRoleComponent } from './groups-details/remove-role/remove-role.component';
import { AddUserGroupComponent } from './groups-details/add-users/add-user.component';
import { AddPermissionComponent } from './add-permission/add-permission.component';
import { RemovePermissionComponent } from './remove-permission/remove-permission.component';




@NgModule({
   declarations: [
      GroupsComponent,
      AddGroupComponent,
      GroupsDetailsComponent,
      AddRoleComponent,
      AddPermissionComponent,
      RemoveRoleComponent,
      AddUserGroupComponent,
      RemoveUserGroupComponent,
      RemoveGroupComponent,
      RemovePermissionComponent
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
      GroupsService
   ],
   exports: [
      GroupsComponent
   ]
})
export class GroupsModule { }
