import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { DatapoolsService } from '../all-datapools/datapools.service';
import { DatapoolDetailsComponent } from './datapool-details.component';

describe('DatapoolDetailsComponent', () => {
  let component: DatapoolDetailsComponent;
  let fixture: ComponentFixture<DatapoolDetailsComponent>;

  let serviceStub: Partial<DatapoolsService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getDatapool(): any {
        return {
          valueChanges: of({
            data: {
              datapool: []
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ DatapoolDetailsComponent ],
      providers: [
        {
          provide: DatapoolsService,
          useValue: serviceStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DatapoolDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
