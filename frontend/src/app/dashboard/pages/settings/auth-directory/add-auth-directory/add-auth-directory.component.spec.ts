import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';

import { AddAuthenticationDirectoryComponent } from './add-auth-directory.component';
import { AuthenticationDirectoryService } from '../auth-directory.service';

describe('AddAuthenticationDirectoryComponent', () => {
  let component: AddAuthenticationDirectoryComponent;
  let fixture: ComponentFixture<AddAuthenticationDirectoryComponent>;

  let serviceStub: Partial<AuthenticationDirectoryService>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        FormsModule
      ],
      declarations: [AddAuthenticationDirectoryComponent ],
      providers: [
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: AuthenticationDirectoryService,
          useValue: serviceStub
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AddAuthenticationDirectoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
