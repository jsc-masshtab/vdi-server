import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { AppRoutingModule } from '../app-routing.module';
import { AddSelectComponent } from './components/add-select/add-select';
import { ButtonRefreshComponent } from './components/button-refresh/button-refresh.component';
import { CheckboxInputComponent } from './components/checkbox-input/checkbox-input.component';
import { PaginationComponent } from './components/pagination/pagination.component';
import { TableComponentComponent } from './components/table-component/table-component.component';
import { TableIntoComponent } from './components/table-into-component/table-into';
import { TabComponent } from './components/tabs/tab/tab.component';
import { TabsComponent } from './components/tabs/tabs.component';
import { FocusMeDirective } from './directives/focusMe.directive';
import { FormForEditComponent } from './forms-dinamic/change-form/form-edit.component';
import { YesNoFormComponent } from './forms-dinamic/yes-no-form/yes-no-form.component';
import { AssignmentTypePipe } from './pipes/assignmentType.pipe';
import { PoolTypePipe } from './pipes/poolType.pipe';
import { StatusPipe } from './pipes/statusEntity.pipe';
import { StatusIconPipe } from './pipes/statusIcon.pipe';
import { TaskTypePipe } from './pipes/taskType.pipe';
import { TranslatePipe } from './pipes/translate.pipe';

const COMPONENTS = [
  TabsComponent,
  TabComponent,
  TableComponentComponent,
  TableIntoComponent,
  PaginationComponent,
  AddSelectComponent,
  ButtonRefreshComponent,
  CheckboxInputComponent
];

const DIRECTIVES = [
  FocusMeDirective
];

const PIPES = [
  StatusPipe,
  StatusIconPipe,
  AssignmentTypePipe,
  TranslatePipe,
  PoolTypePipe,
  TaskTypePipe
];

const FORMS_DINAMIC = [
  FormForEditComponent,
  YesNoFormComponent
];

@NgModule({
  declarations: [
    ...DIRECTIVES,
    ...PIPES,
    ...FORMS_DINAMIC,
    ...COMPONENTS
  ],
  exports: [
    ...DIRECTIVES,
    ...COMPONENTS,
    ...PIPES,
    ...FORMS_DINAMIC,
    MatSelectModule,
    MatCheckboxModule
  ],
  imports: [
    CommonModule,
    FontAwesomeModule,
    MatDialogModule,
    ReactiveFormsModule,
    MatCheckboxModule,
    MatSelectModule,
    AppRoutingModule,
    FormsModule
  ]
})

export class SharedModule {

}
