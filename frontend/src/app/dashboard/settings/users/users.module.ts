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
import { MatCheckboxModule } from '@angular/material';
import { MutateUserComponent } from './user-details/mutate-user/mutate-user.component';



@NgModule({
   declarations: [
      UsersComponent,
      AddUserComponent,
      UserDetailsComponent,
      MutateUserComponent
   ],
   imports: [
      SharedModule,
      CommonModule,
      FontAwesomeModule,
      AppRoutingModule,
      MatDialogModule,
      MatSelectModule,
      ReactiveFormsModule,
      MatCheckboxModule
   ],
   providers: [
      UsersService
   ],
   exports: [
      UsersComponent
   ],
   entryComponents: [
      AddUserComponent,
      MutateUserComponent
   ]
})
export class UsersModule { }
