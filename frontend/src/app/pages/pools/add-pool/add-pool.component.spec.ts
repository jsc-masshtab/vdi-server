import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { of } from 'rxjs';

import { PoolAddComponent } from './add-pool.component';
import { AddPoolService } from './add-pool.service';

describe('PoolAddComponent', () => {
  let component: PoolAddComponent;
  let fixture: ComponentFixture<PoolAddComponent>;

  let addPoolServiceStub: Partial<AddPoolService>;

  beforeEach(waitForAsync(() => {
    addPoolServiceStub = {
      getAllAuthenticationDirectory(): any {
        return {
          valueChanges: of({
            data: {
              auth_dirs: []
            }
          })
        };
      }
    };    

    TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        FormsModule
      ],
      declarations: [ PoolAddComponent ],
      providers: [
        {
          provide: AddPoolService,
          useValue: addPoolServiceStub
        },
        {
          provide: MatDialogRef,
          useValue: {}
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
    fixture = TestBed.createComponent(PoolAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
